if [[ "$(basename -- "$0")" == "maturin.sh" ]]; then
    >&2 echo "ERROR: Don't run $0, source it"
    exit 1
fi


script_dir=$(dirname ${BASH_SOURCE[0]})
export PYTHONPATH=script_dir
export NDSSERVER=localhost:8088

umamba activate ndscope-dev 
export LIBCLANG_PATH=$CONDA_PREFIX/lib
export C_INCLUDE_PATH=$CONDA_PREFIX/include
export CPLUS_INCLUDE_PATH=$CONDA_PREFIX/include

cd ~/projects/dtt_rust
alias mat="maturin develop --features all --target-dir target_maturin"
