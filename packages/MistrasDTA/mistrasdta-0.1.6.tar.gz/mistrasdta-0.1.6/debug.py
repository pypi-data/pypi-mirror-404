# %%
import MistrasDTA

# %%
# rec, wfm = MistrasDTA.read_bin("tests/dta/210527-CH1-15.DTA")
# %%
for i in MistrasDTA._read_bin_generator("tests/dta/210527-CH1-15.DTA", skip_wfm=True):
    True

# %%
