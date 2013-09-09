#pragma version(1)
#pragma rs java_package_name(org.briansimulator.briandroidtemplate)

float dt;
float t;

// START CUSTOM FUNCTIONS //

// PROTOTYPES //

static double exp_rs(double);
static double sqrt_rs(double);
static double pow_rs(double, double);
static int int_rs(bool);
static float randn_rs();
static double clip_rs(double, double, double);

// exp(1) //
static double exp_rs(double value) {
    float value_fl = (float)value;
    return exp(value_fl);
}

// sqrt(1) //
static double sqrt_rs(double value) {
    float value_fl = (float)value;
    return sqrt(value_fl);
}

// pow(2) //
static double pow_rs(double a, double b) {
    float a_fl = (float)a;
    float b_fl = (float)b;
    return pow(a_fl, b_fl);
}

// int(1) //
static int int_rs(bool value) {
    return value ? 1 : 0;
}

// randn() -- normally distributed random var //
static float randn_rs() {
    float x1, x2, w, y1, y2;
    do {
        x1 = 2.0 * rsRand(1.0f) - 1.0;
        x2 = 2.0 * rsRand(1.0f) - 1.0;
        w = x1 * x1 + x2 * x2;
    } while ( w >= 1.0 );

    w = sqrt_rs( (-2.0 * log( w ) ) / w );
    y1 = x1 * w;
    y2 = x2 * w;
    return y1;
}

// clip(3) //
static double clip_rs(double value, double a_min, double a_max) {
    if (value < a_min)
        return a_min;
    if (value > a_max)
        return a_max;
    return value;
}

// END   CUSTOM FUNCTIONS //

%RENDERSCRIPT ARRAYS%

%RENDERSCRIPT CONSTANTS%

int32_t __attribute__((kernel)) update(int32_t _idx) {
    const int _neuron_idx = _idx;
    %STATE UPDATERS%
    return _neuron_idx;
}




