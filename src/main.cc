#include "ir.h"

using namespace scrap::ir;

int main(void) {

    // build test function

    Function func;
    func.num_pos_args = 0;
    func.num_upvalues = 0;

    // x = 1 + 1
    // assert x == 2
    // return x

    // x = 1 + 1
    func.intk_table.push_back(1);
    func.text.push_back(Instruction(Opcode::INTK, 0));
    func.text.push_back(Instruction(Opcode::ADD, 0, 0));

    // assert x == 2
    func.intk_table.push_back(2);
    func.text.push_back(Instruction(Opcode::INTK, 1));
    func.text.push_back(Instruction(Opcode::EQ, 2, 3));
    func.text.push_back(Instruction(Opcode::ASSERT, 4));

    // return x
    func.text.push_back(Instruction(Opcode::RET, 2));

    return 0;
}
