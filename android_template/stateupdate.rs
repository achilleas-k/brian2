#pragma version(1)
#pragma rs java_package_name(org.briansimulator.briandroidtemplate)

float dt;

%RENDERSCRIPT ARRAYS%

%RENDERSCRIPT CONSTANTS%

int32_t __attribute__((kernel)) update(int32_t idx) {
    const int _neuron_idx = idx;
    %STATE UPDATERS%
    return _neuron_idx;
}




