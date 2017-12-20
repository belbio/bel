#!/usr/bin/env bash

# run via: bash <(curl -s https://raw.githubusercontent.com/belbio/bel_lang/master/bin/test_install.sh)

echo
echo "Setting up virtual environment using python 3.6 and activating it"
python3.6 -m venv .venv --prompt 'bel_lang'

activate() {
  source .venv/bin/activate
}

activate

echo
echo
echo "Installing bel_lang package"
# pip install git+https://github.com/belbio/bel_lang@v0.5.3#egg=bel_lang-0.5.3
pip install git+https://github.com/belbio/bel_lang#egg=bel_lang

echo
echo
echo "Confirming belbio_conf.yaml file is available"
if [ ! -e "belbio_conf.yaml" ] && [! -e "~/.belbio_conf" ]
then
    echo "   Missing belbio_conf.yaml or ~/.belbio_conf - will not be able to run test install script"
fi

echo
echo
echo "Please run source .venv/bin/activate to enable the virtualenv if "
echo "   you want to run belstmt commands directly in bash.  The"
echo "   ./bin/run_tests.sh will run inside the virtualenv automatically."
