from .compile_item_system import compile_item_system
from .compile_skill_system import compile_skill_system

def compile():
    compile_skill_system()
    compile_item_system()

if __name__ == '__main__':
    compile()