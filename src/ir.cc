#include "ir.h"

namespace scrap {
namespace ir {

int op_arity(Opcode op) {
    switch (op) {
    case Opcode::NOP:
    case Opcode::JTARG:
    case Opcode::JLOOP:
    case Opcode::SARG:
    case Opcode::RETV:
        return 0;
    case Opcode::MOV:
    case Opcode::JUMP:
    case Opcode::ASSERT:
    case Opcode::NOT:
    case Opcode::BOOL:
    case Opcode::RET:
    case Opcode::INTK:
    case Opcode::STRK:
    case Opcode::BOOLK:
    case Opcode::TYPEK:
    case Opcode::NEG:
    case Opcode::ABS:
    case Opcode::FLOOR:
    case Opcode::CEIL:
    case Opcode::BITNOT:
    case Opcode::LEN:
        return 1;
    case Opcode::CMOV:
    case Opcode::JFOR:
    case Opcode::SETI:
        return 3;
    default:
        return 2;
    }
}

} // end namespace scrap::ir
} // end namespace scrap
