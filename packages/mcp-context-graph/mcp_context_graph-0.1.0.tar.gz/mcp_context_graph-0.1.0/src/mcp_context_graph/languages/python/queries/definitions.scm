; Python definitions query
; Captures function and class definitions

; Function definitions
(function_definition
  name: (identifier) @function.name) @function.definition

; Class definitions
(class_definition
  name: (identifier) @class.name) @class.definition

; Method definitions (inside class)
(class_definition
  body: (block
    (function_definition
      name: (identifier) @method.name) @method.definition))
