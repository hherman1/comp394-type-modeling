# -*- coding: utf-8 -*-

from .types import Type, NoSuchMethod, ClassOrInterface


class Expression(object):
    """
    AST for simple Java expressions. Note that this package deal only with compile-time types;
    this class does not actually _evaluate_ expressions.
    """

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        raise NotImplementedError(type(self).__name__ + " must implement static_type()")

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        raise NotImplementedError(type(self).__name__ + " must implement check_types()")


class Variable(Expression):
    """ An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable
        self.declared_type = declared_type  #: The declared type of the variable (Type)
    
    def static_type(self):
        return self.declared_type
    
    def check_types(self):
        pass


class Literal(Expression):
    """ A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (Type)

    def static_type(self):
        return self.type
    
    def check_types(self):
        pass


class NullLiteral(Literal):
    def __init__(self):
        super().__init__("null", Type.null)
    
    def static_type(self):
        return Type.null
    

def typecheck_arguments_function_call(args, types):
    for (arg, type) in zip(args, types):
        if not arg.static_type().is_subtype_of(type):
            if arg.static_type() == Type.null and type.is_subtype_of(Type.object):
                continue
            else:
                return False
    return True


class MethodCall(Expression):
    """
    A Java method invocation, i.e. `foo.bar(0, 1, 2)`.
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver
        self.receiver = receiver        #: The object whose method we are calling (Expression)
        self.method_name = method_name  #: The name of the method to call (String)
        self.args = args                #: The method arguments (list of Expressions)
    
    def check_types(self):
        for arg in self.args:
            arg.check_types()
        static_type = self.receiver.static_type()
        if static_type == Type.null:
            raise NoSuchMethod("Cannot invoke method " + self.method_name + "() on " + static_type.name)
        if static_type.is_subtype_of(Type.object):
            method = static_type.method_named(self.method_name)
            if len(self.args) != len(method.argument_types):
                raise JavaTypeError("Wrong number of arguments for {}.{}(): expected {}, got {}".format(
                    static_type.name, self.method_name, 
                    len(method.argument_types), len(self.args)
                ))
            if not typecheck_arguments_function_call(self.args, method.argument_types):
                expected_arguments = [expectedType.name for expectedType in method.argument_types]
                received_arguments = [receivedArg.static_type().name for receivedArg in self.args]
                raise JavaTypeError("{}.{}() expects arguments of type ({}), but got ({})".format(
                    static_type.name, self.method_name,
                    ", ".join(expected_arguments),
                    ", ".join(received_arguments)
                    ))
        else:
            raise JavaTypeError("Type {} does not have methods".format(static_type.name))
    
    def static_type(self):
        return self.receiver.static_type().method_named(self.method_name).return_type



class ConstructorCall(Expression):
    """
    A Java object instantiation, i.e. `new Foo(0, 1, 2)`.
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type  #: The type to instantiate (Type)
        self.args = args                            #: Constructor arguments (list of Expressions)

    def check_types(self):
        for arg in self.args:
            arg.check_types()
        if not self.instantiated_type.is_subtype_of(Type.object):
            raise JavaTypeError("Type " + self.instantiated_type.name + " is not instantiable")
        method = self.instantiated_type.constructor
        if len(self.args) != len(method.argument_types):
                raise JavaTypeError("Wrong number of arguments for {} constructor: expected {}, got {}".format(
                    self.instantiated_type.name, 
                    len(method.argument_types), len(self.args)
                ))
        if not typecheck_arguments_function_call(self.args, method.argument_types):
            expected_arguments = [expectedType.name for expectedType in method.argument_types]
            received_arguments = [receivedArg.static_type().name for receivedArg in self.args]
            raise JavaTypeError("{} constructor expects arguments of type ({}), but got ({})"
                .format(self.instantiated_type.name, ", ".join(expected_arguments), ", ".join(received_arguments)))
    
    def static_type(self):
        return self.instantiated_type

class JavaTypeError(Exception):
    """ Indicates a compile-time type error in an expression.
    """
    pass


def names(named_things):
    """ Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
