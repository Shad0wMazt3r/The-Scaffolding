# Crypto - TTPs

Isolated workspace with raw artifacts separate from derived outputs:

```bash
mkdir -p /crypto/<challenge>/{ciphertext,keys,pcaps,transcripts,scripts,sage,evidence,notes,outputs}
python3 -m venv /crypto/<challenge>/.venv
source /crypto/<challenge>/.venv/bin/activate
pip install pycryptodome cryptography angr z3-solver gmpy2
pip install git+https://github.com/RsaCtfTool/RsaCtfTool
sage -n jupyter
jupyter kernelspec install --user $(sage -sh -c 'ls -d $SAGE_VENV/share/jupyter/kernels/sagemath') --name sagemath-ctf
```

Standard isolation: PyCryptodome (`pip install pycryptodome`), cryptography, angr (isolated env), Z3, SageMath Jupyter kernel.

***
