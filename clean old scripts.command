#!/bin/bash

# ============================================
#  🧹 AutoCut - Nettoyage des Anciens Scripts
# ============================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║  🧹  Nettoyage des Anciens Scripts     ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

OLD_SCRIPTS=(
    "Start AutoCut.command"
    "Start AutoCut DEBUG.command"
    "Stop AutoCut.command"
    "Restart AutoCut.command"
    "Start Frontend DEBUG.command"
    "Update and Start AutoCut.command"
    "demarrer_autocut.sh"
    "arreter_autocut.sh"
    "start_backend_only.sh"
    "Démarrer AutoCut.bat"
    "Arrêter AutoCut.bat"
)

FOUND_COUNT=0
FOUND_FILES=()

echo -e "${YELLOW}📋 Recherche des anciens scripts...${NC}"
echo ""

for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        FOUND_COUNT=$((FOUND_COUNT + 1))
        FOUND_FILES+=("$script")
        echo -e "${BLUE}   ✓ Trouvé :${NC} $script"
    fi
done

echo ""

if [ $FOUND_COUNT -eq 0 ]; then
    echo -e "${GREEN}✨ Aucun ancien script trouvé !${NC}"
    echo ""
    read -p "Appuie sur Entrée pour fermer..."
    exit 0
fi

echo -e "${YELLOW}📊 Résumé :${NC}"
echo "   • $FOUND_COUNT ancien(s) script(s) trouvé(s)"
echo ""

echo -e "${RED}⚠️  Ces fichiers seront SUPPRIMÉS${NC}"
echo ""
echo -e "${YELLOW}Continuer ?${NC}"
echo "   [o] Oui, supprimer"
echo "   [a] Archiver"
echo "   [n] Non, annuler"
echo ""
read -p "Ton choix (o/a/n) : " choice

case "$choice" in
    o|O)
        echo ""
        echo -e "${RED}🗑️  Suppression...${NC}"
        echo ""
        for script in "${FOUND_FILES[@]}"; do
            if rm "$script" 2>/dev/null; then
                echo -e "${GREEN}   ✓ Supprimé :${NC} $script"
            fi
        done
        echo ""
        echo -e "${GREEN}✅ Nettoyage terminé !${NC}"
        ;;
    a|A)
        echo ""
        echo -e "${BLUE}📦 Archivage...${NC}"
        echo ""
        ARCHIVE_DIR="old_scripts_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$ARCHIVE_DIR"
        for script in "${FOUND_FILES[@]}"; do
            if mv "$script" "$ARCHIVE_DIR/" 2>/dev/null; then
                echo -e "${GREEN}   ✓ Archivé :${NC} $script"
            fi
        done
        echo ""
        echo -e "${GREEN}✅ Archivage dans :${NC} $ARCHIVE_DIR/"
        ;;
    *)
        echo ""
        echo -e "${YELLOW}❌ Annulé${NC}"
        ;;
esac

echo ""
read -p "Appuie sur Entrée pour fermer..."