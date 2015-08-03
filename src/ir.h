#ifndef SCRAP_IR_H_
#define SCRAP_IR_H_

#include <cstdint>
#include <cassert>

#include <string>
#include <vector>

namespace scrap {
namespace ir {

enum class Opcode : std::uint8_t {

    // utilities
    NOP,    // nop
    PHI,    // phi a, b
    MOV,    // mov a            a
    CMOV,   // cmov c, a, b     c ? a ! b

    // branch targets
    JTARG,  // jtarg            (forward jump target)
    JLOOP,  // jloop            (reverse jump target)
    JFOR,   // jfor i, x, e     for i in x { ... } e: (reverse jump target)

    // branching
    JUMP,   // jump t           goto t (t must be jtarg or jloop or jfor)
    JT,     // jt c, t          if (c) goto t (t must be jtarg)
    JF,     // jf c, t          if (!c) goto t (t must be jtarg)

    // assertions
    ASSERT, // assert c         assert a
    ATYPE,  // atype c, t       c : t
 
    // predicates (result is always boolean)
    EQ,     // eq  a, b         a == b
    NEQ,    // neq a, b         a != b
    IN,     // in  a, b         a in b
    NIN,    // nin a, b         a not in b
    LT,     // lt  a, b         a < b
    GEQ,    // leq a, b         a >= b
    GT,     // gt  a, b         a > b
    LEQ,    // geq a, b         a <= b

    // boolean operations (operands are converted to boolean)
    AND,    // and a, b         a and b
    NOT2,   // not2 a, b        a not b
    OR,     // or  a, b         a or b
    XOR,    // xor a, b         a xor b
    NOT,    // not a            not a
    BOOL,   // bool a           bool(a)

    // function calls
    SARG,   // sarg             (start argument list)
    CALL,   // call f, a        f(A) (where a is 
    RET,    // ret a            return a
    RETV,   // retv             return (void)
    TCALL,  // tcall f, a       return f(a)

    // constants
    INTK,   // intk i           load integer constant #i
    STRK,   // strk i           load string constant #i
    BOOLK,  // boolk x          load false (x==0) or true (x==1)
    TYPEK,  // typek i          load type constant #i

    // arithmetic operations
    ADD,    // add a, b         a + b
    SUB,    // sub a, b         a - b
    MUL,    // mul a, b         a * b
    FDIV,   // fdiv a, b        a // b
    MOD,    // mod a, b         a % b
    POW,    // pow a, b         a ** b
    DIV,    // div a, b         a / b
    MIN,    // min a, b         min(a, b)
    MAX,    // max a, b         max(a, b)
    NEG,    // neg a            -a
    ABS,    // abs a            abs(a)
    FLOOR,  // floor a          floor(a)
    CEIL,   // ceil a           ceil(a)

    // bitwise operations
    BITAND, // bitand a, b      a & b
    BITOR,  // bitor  a, b      a | b
    BITXOR, // bitxor a, b      a ^ b
    BITANOT,// bitanot a, b     a &~ b
    BITSHR, // bitshr a, b      a >> b
    BITSHL, // bitshl a, b      a << b
    BITNOT, // bitnot a         ~a

    // string operations
    CAT,    // cat a, b         a .. b
    FMT,    // fmt a, b         a %% b

    // indexing operations
    GETI,   // geti a, i        a[i]
    SETI,   // seti a, i, v     a[i] = b
    DELI,   // deli a, i        del a[i]

    // collection operations
    LEN,    // len a            len(a)
};

int op_arity(Opcode op) __attribute__((pure));
bool op_has_result(Opcode op) __attribute__((pure));
bool op_is_mutator(Opcode op) __attribute__((pure));

inline bool op_is_cond_branch(Opcode op) {
    return op == Opcode::JT || op == Opcode::JF || op == Opcode::JFOR;
}

inline bool op_is_uncond_branch(Opcode op) { 
    return op == Opcode::JUMP;
}

struct Instruction {
    Opcode op;
    uint16_t arg[3];
    
    Instruction(Opcode op_) :
      op(op_), arg{0, 0, 0} {
        assert(op_arity(op_) == 0);
    }

    Instruction(Opcode op_, uint16_t arg0) : 
      op(op_), arg{arg0, 0, 0} {
        assert(op_arity(op_) == 1);
    }
    
    Instruction(Opcode op_, uint16_t arg0, uint16_t arg1) :
      op(op_), arg{arg0, arg1, 0} {
        assert(op_arity(op_) == 2);
    }
    
    Instruction(Opcode op_, uint16_t arg0, uint16_t arg1, uint16_t arg2) :
      op(op_), arg{arg0, arg1, arg2} {
        assert(op_arity(op_) == 3);
    }
};

struct Function {
    int num_pos_args;
    int num_upvalues;

    std::vector<std::string> strk_table;
    std::vector<int32_t> intk_table;
    std::vector<Instruction> text;
};

} // end namespace scrap::ir

} // end namespace scrap

#endif//SCRAP_IR_H_
