from __future__ import annotations

import os
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from tree_sitter_language_pack import get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    raise ImportError("tree-sitter-language-pack is required for code analysis. Install it with: pip install tree-sitter-language-pack")


@dataclass
class CodeReference:
    type: str
    name: str
    context: Optional[str] = None


class FastCodeAnalyzer:
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise RuntimeError("tree-sitter-languages is not available")
        self.cache: Dict[str, List[CodeReference]] = {}
        self._max_cache_size = 1000
        self.parsers: Dict[str, any] = {}
        self._init_parsers()

    def _init_parsers(self):
        try:
            self.parsers['python'] = get_parser('python')
            self.parsers['javascript'] = get_parser('javascript')
            self.parsers['typescript'] = get_parser('typescript')
            self.parsers['java'] = get_parser('java')
            self.parsers['go'] = get_parser('go')
            self.parsers['rust'] = get_parser('rust')
        except Exception as e:
            raise RuntimeError(f"Failed to initialize tree-sitter parsers: {e}")

    def extract_references_fast(self, file_path: str) -> List[CodeReference]:
        if file_path in self.cache:
            return self.cache[file_path]

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.py':
                refs = self._parse_python_ast(file_path)
            elif ext in ['.js', '.jsx', '.mjs', '.cjs']:
                refs = self._parse_javascript_ast(file_path)
            elif ext in ['.ts', '.tsx']:
                refs = self._parse_typescript_ast(file_path)
            elif ext == '.java':
                refs = self._parse_java_ast(file_path)
            elif ext == '.go':
                refs = self._parse_go_ast(file_path)
            elif ext == '.rs':
                refs = self._parse_rust_ast(file_path)
            else:
                return []

            self._cache_references(file_path, refs)
            return refs

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def _parse_python_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['python'].parse(bytes(content, 'utf-8'))
            root_node = tree.root_node

            def walk(node):
                if node.type == 'import_statement':
                    for child in node.children:
                        if child.type == 'dotted_name':
                            refs.append(CodeReference(
                                type='import',
                                name=child.text.decode('utf-8'),
                                context=f"import {child.text.decode('utf-8')}"
                            ))

                elif node.type == 'import_from_statement':
                    module_name = None
                    for child in node.children:
                        if child.type == 'dotted_name' and not module_name:
                            module_name = child.text.decode('utf-8')
                            refs.append(CodeReference(
                                type='import',
                                name=module_name,
                                context=f"from {module_name}"
                            ))
                        elif child.type == 'dotted_name' and module_name:
                            refs.append(CodeReference(
                                type='import',
                                name=child.text.decode('utf-8'),
                                context=f"from {module_name} import {child.text.decode('utf-8')}"
                            ))
                        elif child.type == 'identifier' and module_name:
                            refs.append(CodeReference(
                                type='import',
                                name=child.text.decode('utf-8'),
                                context=f"from {module_name} import {child.text.decode('utf-8')}"
                            ))

                elif node.type == 'class_definition':
                    for child in node.children:
                        if child.type == 'identifier':
                            refs.append(CodeReference(
                                type='class_def',
                                name=child.text.decode('utf-8'),
                                context=f"class {child.text.decode('utf-8')}"
                            ))
                            break

                elif node.type == 'function_definition':
                    for child in node.children:
                        if child.type == 'identifier':
                            func_name = child.text.decode('utf-8')
                            if not func_name.startswith('_'):
                                refs.append(CodeReference(
                                    type='function_def',
                                    name=func_name,
                                    context=f"def {func_name}"
                                ))
                            break

                elif node.type == 'call':
                    func_node = node.child_by_field_name('function')
                    if func_node:
                        if func_node.type == 'identifier':
                            func_name = func_node.text.decode('utf-8')
                            if not func_name.startswith('_'):
                                refs.append(CodeReference(
                                    type='function_call',
                                    name=func_name
                                ))
                        elif func_node.type == 'attribute':
                            attr_node = func_node.child_by_field_name('attribute')
                            if attr_node:
                                refs.append(CodeReference(
                                    type='function_call',
                                    name=attr_node.text.decode('utf-8')
                                ))

                for child in node.children:
                    walk(child)

            walk(root_node)

        except Exception as e:
            print(f"Error in _parse_python_ast: {e}")

        return self._deduplicate_references(refs)

    def _parse_javascript_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['javascript'].parse(bytes(content, 'utf-8'))
            refs = self._extract_js_refs_treesitter(tree.root_node)

        except Exception as e:
            print(f"Error in _parse_javascript_ast: {e}")

        return self._deduplicate_references(refs)

    def _parse_typescript_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['typescript'].parse(bytes(content, 'utf-8'))
            refs = self._extract_js_refs_treesitter(tree.root_node)

        except Exception as e:
            print(f"Error in _parse_typescript_ast: {e}")

        return self._deduplicate_references(refs)

    def _extract_js_refs_treesitter(self, root_node) -> List[CodeReference]:
        refs = []

        def walk(node):
            if node.type == 'import_statement':
                source_node = node.child_by_field_name('source')
                if source_node:
                    import_path = source_node.text.decode('utf-8').strip('"\'')
                    module_name = import_path.split('/')[-1].replace('.js', '').replace('.ts', '')
                    refs.append(CodeReference(
                        type='import',
                        name=module_name
                    ))

            elif node.type == 'call_expression':
                func_node = node.child_by_field_name('function')
                if func_node and func_node.text.decode('utf-8') == 'require':
                    args_node = node.child_by_field_name('arguments')
                    if args_node:
                        for child in args_node.children:
                            if child.type == 'string':
                                require_path = child.text.decode('utf-8').strip('"\'')
                                module_name = require_path.split('/')[-1].replace('.js', '')
                                refs.append(CodeReference(
                                    type='import',
                                    name=module_name
                                ))
                                break

            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    refs.append(CodeReference(
                        type='class_def',
                        name=name_node.text.decode('utf-8')
                    ))

            elif node.type in ['function_declaration', 'method_definition']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    func_name = name_node.text.decode('utf-8')
                    if not func_name.startswith('_'):
                        refs.append(CodeReference(
                            type='function_def',
                            name=func_name
                        ))

            elif node.type in ['lexical_declaration', 'variable_declaration']:
                for child in node.children:
                    if child.type == 'variable_declarator':
                        name_node = child.child_by_field_name('name')
                        value_node = child.child_by_field_name('value')
                        if name_node and value_node and value_node.type in ['arrow_function', 'function']:
                            refs.append(CodeReference(
                                type='function_def',
                                name=name_node.text.decode('utf-8')
                            ))

            elif node.type == 'call_expression':
                func_node = node.child_by_field_name('function')
                if func_node:
                    func_name = ''
                    if func_node.type == 'identifier':
                        func_name = func_node.text.decode('utf-8')
                    elif func_node.type == 'member_expression':
                        prop_node = func_node.child_by_field_name('property')
                        if prop_node:
                            func_name = prop_node.text.decode('utf-8')
                    
                    if func_name and func_name not in ['if', 'for', 'while', 'switch', 'catch', 'require']:
                        refs.append(CodeReference(
                            type='function_call',
                            name=func_name
                        ))

            for child in node.children:
                walk(child)

        walk(root_node)
        return refs

    def _parse_java_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['java'].parse(bytes(content, 'utf-8'))
            root_node = tree.root_node

            def walk(node):
                if node.type == 'import_declaration':
                    for child in node.children:
                        if child.type in ['scoped_identifier', 'identifier']:
                            full_path = child.text.decode('utf-8')
                            class_name = full_path.split('.')[-1]
                            refs.append(CodeReference(
                                type='import',
                                name=class_name
                            ))
                            break

                elif node.type == 'class_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        refs.append(CodeReference(
                            type='class_def',
                            name=name_node.text.decode('utf-8')
                        ))

                elif node.type == 'method_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        refs.append(CodeReference(
                            type='function_def',
                            name=name_node.text.decode('utf-8')
                        ))

                for child in node.children:
                    walk(child)

            walk(root_node)

        except Exception as e:
            print(f"Error in _parse_java_ast: {e}")

        return self._deduplicate_references(refs)

    def _parse_go_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['go'].parse(bytes(content, 'utf-8'))
            root_node = tree.root_node

            def walk(node):
                if node.type == 'import_spec':
                    path_node = node.child_by_field_name('path')
                    if path_node:
                        import_path = path_node.text.decode('utf-8').strip('"')
                        package_name = import_path.split('/')[-1]
                        refs.append(CodeReference(
                            type='import',
                            name=package_name
                        ))

                elif node.type == 'type_declaration':
                    for child in node.children:
                        if child.type == 'type_spec':
                            name_node = child.child_by_field_name('name')
                            if name_node:
                                refs.append(CodeReference(
                                    type='class_def',
                                    name=name_node.text.decode('utf-8')
                                ))

                elif node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        refs.append(CodeReference(
                            type='function_def',
                            name=name_node.text.decode('utf-8')
                        ))

                for child in node.children:
                    walk(child)

            walk(root_node)

        except Exception as e:
            print(f"Error in _parse_go_ast: {e}")

        return self._deduplicate_references(refs)

    def _parse_rust_ast(self, file_path: str) -> List[CodeReference]:
        refs = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = self.parsers['rust'].parse(bytes(content, 'utf-8'))
            root_node = tree.root_node

            def walk(node):
                if node.type == 'use_declaration':
                    identifiers = []
                    
                    def collect_identifiers(n):
                        if n.type == 'identifier':
                            identifiers.append(n)
                        for child in n.children:
                            collect_identifiers(child)
                    
                    collect_identifiers(node)
                    
                    if identifiers:
                        last_name = identifiers[-1]
                        refs.append(CodeReference(
                            type='import',
                            name=last_name.text.decode('utf-8')
                        ))

                elif node.type == 'struct_item':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        refs.append(CodeReference(
                            type='class_def',
                            name=name_node.text.decode('utf-8')
                        ))

                elif node.type == 'function_item':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        refs.append(CodeReference(
                            type='function_def',
                            name=name_node.text.decode('utf-8')
                        ))

                for child in node.children:
                    walk(child)

            walk(root_node)

        except Exception as e:
            print(f"Error in _parse_rust_ast: {e}")

        return self._deduplicate_references(refs)

    def _deduplicate_references(self, refs: List[CodeReference]) -> List[CodeReference]:
        seen = {}
        for ref in refs:
            key = (ref.type, ref.name)
            if key not in seen:
                seen[key] = ref
        return list(seen.values())

    def _cache_references(self, file_path: str, refs: List[CodeReference]):
        if len(self.cache) >= self._max_cache_size:
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        self.cache[file_path] = refs

    def clear_cache(self):
        self.cache.clear()

    def get_top_references(
        self,
        file_paths: List[str],
        n: int = 8,
        ref_types: Optional[List[str]] = None
    ) -> List[CodeReference]:
        all_refs = []

        for file_path in file_paths:
            refs = self.extract_references_fast(file_path)
            if ref_types:
                refs = [r for r in refs if r.type in ref_types]
            all_refs.extend(refs)

        unique_refs = self._deduplicate_references(all_refs)
        return unique_refs[:n]
