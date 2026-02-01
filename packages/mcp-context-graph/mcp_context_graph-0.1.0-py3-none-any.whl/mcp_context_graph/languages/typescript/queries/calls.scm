; TypeScript/JavaScript calls query
; Captures function/method call expressions

; Simple function calls: foo()
(call_expression
  function: (identifier) @call.name) @call.expression

; Method calls: obj.method()
(call_expression
  function: (member_expression
    object: (identifier) @call.object
    property: (property_identifier) @call.method)) @call.expression

; Chained method calls: obj.prop.method()
(call_expression
  function: (member_expression
    property: (property_identifier) @call.method)) @call.expression

; New expressions: new Class()
(new_expression
  constructor: (identifier) @call.constructor) @call.expression

; Await calls: await foo()
(await_expression
  (call_expression
    function: (identifier) @call.name)) @call.expression

; IIFE: (function() {})()
(call_expression
  function: (parenthesized_expression
    (function_expression))) @call.iife

; Arrow IIFE: (() => {})()
(call_expression
  function: (parenthesized_expression
    (arrow_function))) @call.iife
