cd verilator
sudo make uninstall
git checkout -v
autoconf
make -j `nproc`
sudo make install