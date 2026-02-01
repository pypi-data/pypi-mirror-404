; Python imports query
; Captures import statements

; Simple import: import foo
(import_statement
  name: (dotted_name) @import.module) @import.statement

; From import: from foo import bar
(import_from_statement
  module_name: (dotted_name) @import.module
  name: (dotted_name) @import.name) @import.statement

; From import with alias: from foo import bar as baz
(import_from_statement
  module_name: (dotted_name) @import.module
  name: (aliased_import
    name: (dotted_name) @import.name
    alias: (identifier) @import.alias)) @import.statement

; Import with alias: import foo as bar
(import_statement
  name: (aliased_import
    name: (dotted_name) @import.module
    alias: (identifier) @import.alias)) @import.statement

; Wildcard import: from foo import *
(import_from_statement
  module_name: (dotted_name) @import.module
  (wildcard_import) @import.wildcard) @import.statement
