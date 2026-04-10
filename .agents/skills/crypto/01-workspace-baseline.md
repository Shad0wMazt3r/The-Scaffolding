# Crypto - TTPs

Use an isolated workspace and keep raw artifacts separate from derived outputs:

```bash
mkdir -p /crypto/<challenge>/{ciphertext,keys,pcaps,transcripts,scripts,sage,evidence,notes,outputs}
python3 -m venv /crypto/<challenge>/.venv
source /crypto/<challenge>/.venv/bin/activate
pip install --upgrade pip
pip install pycryptodome cryptography angr z3-solver gmpy2
pip install git+https://github.com/RsaCtfTool/RsaCtfTool
sage -n jupyter
jupyter kernelspec list
jupyter kernelspec install --user $(sage -sh -c 'ls -d $SAGE_VENV/share/jupyter/kernels/sagemath') --name sagemath-ctf
```

That baseline matches the documented install paths for PyCryptodome, `cryptography`, `angr`, Z3’s Python bindings, SageMath’s Jupyter kernel, and RsaCtfTool’s preferred virtual-environment workflow.  PyCryptodome installs under `Crypto` with `pip install pycryptodome`, `cryptography` is typically installed with `pip install cryptography`, `angr` is recommended inside an isolated environment, and SageMath can be launched with `sage -n jupyter` and registered into an existing Jupyter install with `jupyter kernelspec install --user ...`. [arxiv](https://arxiv.org/pdf/2306.16812.pdf)

