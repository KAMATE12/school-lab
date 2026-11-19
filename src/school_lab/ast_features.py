"""Scoped structural baseline; see AST_METHOD_FR.md for policy and limits."""
import ast
import hashlib
import json
import sys
from dataclasses import dataclass, field

from school_lab.ast_scopes import NameScope
from school_lab.errors import SubmissionError
from school_lab.token_evidence import find_template_lines

AST_VERSION = "1.0"


# RU: Связываем локальные имена с родительской областью.
# EN: Link local names to the enclosing scope.
@dataclass
class _Scope:
    number: int
    parent: "_Scope | None"
    names: NameScope = field(default_factory=NameScope)
    bindings: set[str] = field(default_factory=set)


# RU: Сохраняем признаки и исходные диапазоны строк.
# EN: Preserve features and original source line ranges.
@dataclass(frozen=True)
class AstOccurrence:
    key: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class PreparedAstCode:
    keys: frozenset[str]
    occurrences: tuple[AstOccurrence, ...]
    template_lines: tuple[int, ...]
    config_hash: str
    method_version: str = AST_VERSION


# RU: Сначала собираем связи имён, затем выполняем переименование.
# EN: Collect name bindings first, then perform renaming.
class _Normalizer:
    def __init__(self) -> None:
        self.scopes = [_Scope(0, None)]
        self.events = []

    def child(self, parent: _Scope) -> _Scope:
        scope = _Scope(len(self.scopes), parent)
        self.scopes.append(scope)
        return scope

    def event(self, node, attribute, name, scope, binding=False):
        if binding:
            scope.bindings.add(name)
        self.events.append((node, attribute, name, scope))

    def visit(self, node, scope):
        # RU: Неподдерживаемые конструкции дают явную ошибку.
        # EN: Unsupported constructs produce an explicit error.
        unsupported = (
            ast.ClassDef, ast.Global, ast.Nonlocal, ast.NamedExpr,
            ast.Match, ast.TypeAlias,
        )
        if isinstance(node, unsupported) or type(node).__name__ == "TemplateStr":
            raise SubmissionError(
                code="unsupported_ast", field="code",
                message="Конструкция не поддерживается / Unsupported AST construct: "
                + type(node).__name__,
            )
        if getattr(node, "type_params", []):
            raise SubmissionError(
                code="unsupported_ast", field="code",
                message="Параметры типов не поддерживаются / Type parameters are unsupported",
            )
        if isinstance(node, ast.Name):
            self.event(node, "id", node.id, scope,
                       isinstance(node.ctx, (ast.Store, ast.Del)))
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if not isinstance(node, ast.Lambda):
                self.event(node, "name", node.name, scope, True)
                for decorator in node.decorator_list:
                    self.visit(decorator, scope)
            # RU: Значения по умолчанию относятся к внешней области.
            # EN: Defaults belong to the enclosing scope.
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                if default is not None:
                    self.visit(default, scope)
            local = self.child(scope)
            parameters = [*node.args.posonlyargs, *node.args.args,
                          *node.args.kwonlyargs]
            if node.args.vararg is not None:
                parameters.append(node.args.vararg)
            if node.args.kwarg is not None:
                parameters.append(node.args.kwarg)
            for argument in parameters:
                self.event(argument, "arg", argument.arg, local, True)
            # RU: Аннотации сохраняем дословно как часть структуры.
            # EN: Preserve annotations literally as part of the structure.
            body = [node.body] if isinstance(node, ast.Lambda) else node.body
            for statement in body:
                self.visit(statement, local)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            # RU: Первый источник читается во внешней области.
            # EN: The first iterable is evaluated in the enclosing scope.
            self.visit(node.generators[0].iter, scope)
            local = self.child(scope)
            for index, generator in enumerate(node.generators):
                self.visit(generator.target, local)
                if index:
                    self.visit(generator.iter, local)
                for condition in generator.ifs:
                    self.visit(condition, local)
            if isinstance(node, ast.DictComp):
                self.visit(node.key, local)
                self.visit(node.value, local)
            else:
                self.visit(node.elt, local)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    raise SubmissionError(
                        code="unsupported_ast", field="code",
                        message="Импорт * не поддерживается / Star imports are unsupported",
                    )
                # RU: Сохраняем путь импорта; нормализуем локальное имя.
                # EN: Preserve the import path; normalize the local binding.
                name = alias.asname or (
                    alias.name.split(".")[0] if isinstance(node, ast.Import)
                    else alias.name
                )
                self.event(alias, "asname", name, scope, True)
            return
        if isinstance(node, ast.ExceptHandler) and node.name is not None:
            self.event(node, "name", node.name, scope, True)
        if isinstance(node, ast.AnnAssign):
            self.visit(node.target, scope)
            if node.value is not None:
                self.visit(node.value, scope)
            return
        for child in ast.iter_child_nodes(node):
            self.visit(child, scope)

    def normalize(self, tree):
        self.visit(tree, self.scopes[0])
        # RU: Нумеруем по исходному порядку, а не по порядку ast.walk.
        # EN: Number names by source order, not by ast.walk order.
        self.events.sort(key=lambda event: (
            event[0].lineno, event[0].col_offset,
        ))
        for node, attribute, original, scope in self.events:
            owner = scope
            while owner is not None and original not in owner.bindings:
                owner = owner.parent
            if owner is None:
                # RU: Сохраняем различие между внешними именами, например sum и max.
                # EN: Preserve differences between external names, such as sum and max.
                replacement = "external:" + original
            else:
                replacement = f"scope{owner.number}:" + owner.names.normalize(original)
            setattr(node, attribute, replacement)
        return tree


# RU: Получаем стабильную структуру без координат и без запуска кода.
# EN: Obtain a stable structure without coordinates or code execution.
def _structure(node):
    if isinstance(node, ast.AST):
        # RU: Пустые поля сохраняем одинаково в разных версиях ast.dump.
        # EN: Keep empty fields consistent across ast.dump versions.
        return [type(node).__name__, [
            [name, _structure(value)] for name, value in ast.iter_fields(node)
        ]]
    if isinstance(node, list):
        return [_structure(item) for item in node]
    if node is None or isinstance(node, (str, bool, int)):
        return node
    return [type(node).__name__, repr(node)]


def _key(node):
    return json.dumps(_structure(node), ensure_ascii=False, separators=(",", ":"))


# RU: Подготавливаем AST один раз для многократного сравнения.
# EN: Prepare the AST once for repeated comparison.
def prepare_ast_code(code: str, allowed_template: str = "") -> PreparedAstCode:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise SubmissionError(
            code="invalid_code", field="code",
            message=f"Ошибка синтаксиса / Invalid Python syntax: line={error.lineno}: {error.msg}",
        ) from error
    excluded = find_template_lines(code, allowed_template)

    # RU: Удаляем целые инструкции шаблона до нормализации имён.
    # EN: Remove whole template statements before normalizing names.
    class RemoveTemplate(ast.NodeTransformer):
        def visit(self, node):
            if isinstance(node, ast.stmt):
                lines = range(node.lineno, node.end_lineno + 1)
                if all(line in excluded for line in lines):
                    return None
            return super().visit(node)

    tree = RemoveTemplate().visit(tree)
    tree = _Normalizer().normalize(tree)
    occurrences = []
    # RU: Признаки — поддеревья инструкций, не пересекающие шаблон.
    # EN: Features are statement subtrees that do not cross template lines.
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        lines = range(node.lineno, node.end_lineno + 1)
        if any(line in excluded for line in lines):
            continue
        occurrences.append(AstOccurrence(_key(node), node.lineno, node.end_lineno))
    occurrences.sort(key=lambda item: (item.start_line, item.end_line, item.key))
    configuration = json.dumps({
        "method": "ast_statement_jaccard", "version": AST_VERSION,
        "template": allowed_template,
        "python": list(sys.version_info[:2]),
    }, sort_keys=True, ensure_ascii=False)
    config_hash = hashlib.sha256(configuration.encode("utf-8")).hexdigest()
    return PreparedAstCode(
        frozenset(item.key for item in occurrences), tuple(occurrences),
        tuple(sorted(excluded)), config_hash,
    )
