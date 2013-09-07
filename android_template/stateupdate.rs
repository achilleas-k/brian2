#pragma version(1)
#pragma rs java_package_name(org.briansimulator.briandroidtemplate)

float dt;
float t;

float x1, x2, w, y1, y2;
  ranf should be a uniform 0-1
  do {
  x1 = 2.0 * ranf() - 1.0;
  x2 = 2.0 * ranf() - 1.0;
  w = x1 * x1 + x2 * x2;
  } while ( w >= 1.0 );

  w = sqrt( (-2.0 * log( w ) ) / w );
  y1 = x1 * w;
  y2 = x2 * w;

%RENDERSCRIPT ARRAYS%

%RENDERSCRIPT CONSTANTS%

int32_t __attribute__((kernel)) update(int32_t _idx) {
    const int _neuron_idx = _idx;
    %STATE UPDATERS%
    return _neuron_idx;
}




