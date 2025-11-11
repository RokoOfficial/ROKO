#!/usr/bin/env python3
"""
Launcher principal - aponta para CodeR
"""
import sys
import os

# Adicionar CodeR ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CodeR'))

# Importar e executar o app principal
from CodeR.app import main

if __name__ == "__main__":
    main()
