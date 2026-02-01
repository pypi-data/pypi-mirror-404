; TypeScript/JavaScript imports query
; Captures import statements

; Named imports: import { foo } from 'module'
(import_statement
  (import_clause
    (named_imports
      (import_specifier
        name: (identifier) @import.name)))
  source: (string) @import.source) @import.statement

; Default imports: import foo from 'module'
(import_statement
  (import_clause
    (identifier) @import.default)
  source: (string) @import.source) @import.statement

; Namespace imports: import * as foo from 'module'
(import_statement
  (import_clause
    (namespace_import
      (identifier) @import.namespace))
  source: (string) @import.source) @import.statement

; Side-effect imports: import 'module'
(import_statement
  source: (string) @import.source) @import.statement

; Dynamic imports: import('module')
(call_expression
  function: (import)
  arguments: (arguments
    (string) @import.dynamic)) @import.expression

; CommonJS require: const foo = require('module')
(lexical_declaration
  (variable_declarator
    name: (identifier) @import.name
    value: (call_expression
      function: (identifier) @_require
      arguments: (arguments
        (string) @import.source))))

; Export from: export { foo } from 'module'
(export_statement
  (export_clause)
  source: (string) @import.reexport) @export.statement

; Export all: export * from 'module'
(export_statement
  source: (string) @import.reexport) @export.statement
