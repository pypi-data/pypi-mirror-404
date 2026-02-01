; TypeScript/JavaScript definitions query
; Captures function and class definitions

; Function declarations: function foo() {}
(function_declaration
  name: (identifier) @function.name) @function.definition

; Arrow functions assigned to variables: const foo = () => {}
(lexical_declaration
  (variable_declarator
    name: (identifier) @function.name
    value: (arrow_function))) @function.definition

; Arrow functions in variable declarations: var foo = () => {}
(variable_declaration
  (variable_declarator
    name: (identifier) @function.name
    value: (arrow_function))) @function.definition

; Function expressions assigned to variables: const foo = function() {}
(lexical_declaration
  (variable_declarator
    name: (identifier) @function.name
    value: (function_expression))) @function.definition

; Class declarations: class Foo {}
(class_declaration
  name: (identifier) @class.name) @class.definition

; Method definitions inside class
(class_declaration
  body: (class_body
    (method_definition
      name: (property_identifier) @method.name) @method.definition))

; TypeScript: interface declarations
(interface_declaration
  name: (type_identifier) @interface.name) @interface.definition

; TypeScript: type alias declarations
(type_alias_declaration
  name: (type_identifier) @type.name) @type.definition

; Export function declarations: export function foo() {}
(export_statement
  declaration: (function_declaration
    name: (identifier) @function.name)) @function.definition

; Export class declarations: export class Foo {}
(export_statement
  declaration: (class_declaration
    name: (identifier) @class.name)) @class.definition
