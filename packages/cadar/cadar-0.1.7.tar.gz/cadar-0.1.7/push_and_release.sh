#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════"
echo "  CaDaR - Push Code and Create Release v0.1.0"
echo "════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "Cargo.toml" ] || [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Not in CaDaR root directory${NC}"
    exit 1
fi

# Step 1: Push to main branch
echo -e "${YELLOW}Step 1: Pushing code to GitHub main branch...${NC}"
echo ""

# Try to push
if git push -u origin main 2>&1 | tee /tmp/git_push.log; then
    echo -e "${GREEN}✓ Code pushed to main branch successfully!${NC}"
    echo ""
else
    EXIT_CODE=${PIPESTATUS[0]}

    if [ $EXIT_CODE -eq 128 ]; then
        echo -e "${RED}✗ Authentication required!${NC}"
        echo ""
        echo "GitHub authentication is needed. Please choose an option:"
        echo ""
        echo "Option 1: Use SSH (Recommended)"
        echo "  git remote set-url origin git@github.com:Oit-Technologies/CaDaR.git"
        echo "  git push -u origin main"
        echo ""
        echo "Option 2: Use GitHub CLI"
        echo "  gh auth login"
        echo "  git push -u origin main"
        echo ""
        echo "Option 3: Use Personal Access Token"
        echo "  1. Create token at: https://github.com/settings/tokens"
        echo "  2. Run: git push -u origin main"
        echo "  3. Username: your-github-username"
        echo "  4. Password: paste-your-token"
        echo ""
        echo "After authenticating, run this script again."
        exit 1
    else
        echo -e "${RED}✗ Push failed with error code $EXIT_CODE${NC}"
        cat /tmp/git_push.log
        exit 1
    fi
fi

# Step 2: Create release tag
echo -e "${YELLOW}Step 2: Creating release tag v0.1.0...${NC}"
echo ""

# Check if tag already exists
if git rev-parse v0.1.0 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Tag v0.1.0 already exists${NC}"
    echo "Do you want to delete and recreate it? (y/N)"
    read -r REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d v0.1.0
        git push origin :refs/tags/v0.1.0 2>/dev/null || true
        echo -e "${GREEN}✓ Deleted existing tag${NC}"
    else
        echo "Skipping tag creation"
        exit 0
    fi
fi

# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0 - Initial CaDaR release

Features:
- Bidirectional Darija transliteration (Arabic ↔ Latin)
- 6-stage FST-style pipeline with ICR
- Python API: ara2bizi, bizi2ara, ara2ara, bizi2bizi
- Moroccan Darija support
- Comprehensive documentation
- 41 passing unit tests

This is the first stable release of CaDaR.
"

echo -e "${GREEN}✓ Created tag v0.1.0${NC}"
echo ""

# Step 3: Push tag to trigger GitHub Actions
echo -e "${YELLOW}Step 3: Pushing tag to GitHub (this triggers automation)...${NC}"
echo ""

if git push origin v0.1.0; then
    echo -e "${GREEN}✓ Tag pushed successfully!${NC}"
    echo ""
else
    echo -e "${RED}✗ Failed to push tag${NC}"
    exit 1
fi

# Success message
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✓ Success! Release v0.1.0 initiated${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "GitHub Actions are now running. This will:"
echo ""
echo "  📦 Build wheels for all platforms"
echo "  🚀 Publish to PyPI"
echo "  📚 Build and deploy documentation"
echo "  🎉 Create GitHub release"
echo ""
echo "Monitor progress at:"
echo "  https://github.com/Oit-Technologies/CaDaR/actions"
echo ""
echo "After a few minutes, check:"
echo "  📦 PyPI: https://pypi.org/project/cadar/"
echo "  📚 Docs: https://oit-technologies.github.io/CaDaR/"
echo "  🎉 Release: https://github.com/Oit-Technologies/CaDaR/releases/tag/v0.1.0"
echo ""
echo "Installation will be available via:"
echo "  pip install cadar"
echo ""
