#!/bin/bash
# Este script actualizará tu VPS desde Git

# Realiza un pull para obtener los últimos cambios
git pull origin main  # Asegúrate de usar la rama correcta
git pull --rebase