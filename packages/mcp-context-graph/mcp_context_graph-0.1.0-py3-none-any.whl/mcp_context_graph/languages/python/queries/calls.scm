; Python calls query
; Captures function/method call expressions

; Simple function calls: foo()
(call
  function: (identifier) @call.name) @call.expression

; Attribute method calls: obj.method()
(call
  function: (attribute
    object: (identifier) @call.object
    attribute: (identifier) @call.method)) @call.expression

; Chained attribute calls: obj.attr.method()
(call
  function: (attribute
    attribute: (identifier) @call.method)) @call.expression
