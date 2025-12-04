#!/bin/bash
# Demo script for Chronicles of Aethermoor Phase 1

echo "========================================="
echo "CHRONICLES OF AETHERMOOR - PHASE 1 DEMO"
echo "========================================="
echo ""
echo "This demo showcases the Phase 1 foundation systems:"
echo "  ✓ Core data structures"
echo "  ✓ Game state management"
echo "  ✓ Save/load system"
echo "  ✓ Turn progression"
echo "  ✓ Basic game loop"
echo ""
echo "Starting game..."
echo ""

# Navigate to project directory
cd ~/chronicles-of-aethermoor

# Run game with automated inputs for demo
# Input: 1 (New Game), TestPlayer, TestNation, 2 (Normal), 1 (View Status), 2 (Advance Turn), 2, 2, 3 (Save), 1 (Slot 1), 4 (Return to menu)
echo -e "1\nTestPlayer\nTestNation\n2\n1\n2\n2\n2\n3\n1\n4" | timeout 10 ./venv/bin/python -m src.main

echo ""
echo "========================================="
echo "DEMO COMPLETE"
echo "========================================="
echo ""
echo "Phase 1 systems successfully demonstrated!"
echo ""
echo "To play manually:"
echo "  cd ~/chronicles-of-aethermoor"
echo "  ./venv/bin/python -m src.main"
echo ""
