package org.briansimulator.briandroidtemplate;

import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.Arrays;

import android.content.Context;
import android.os.AsyncTask;
import android.os.Environment;
import android.renderscript.Allocation;
import android.renderscript.Element;
import android.renderscript.RenderScript;
import android.util.Log;


/**
 * The base code generation template for BrianDROID simulations
 */
public class CodegenTemplate extends AsyncTask<Void, String, Void> {

    private final static String LOGID = "org.briansimulator.briandroidtemplate.CodegenTemplate";
    Context bdContext;
    float _duration;
    float t;
    %JAVA TIMESTEP%
    int simstate = 0;

    long runtimeDuration = -1;

    private String simulationStatus;
    private final String DESCRIPTION = "%%% SIMULATION DESCRIPTION %%%";

    // renderscript engine objects
    private RenderScript mRS;
    private ScriptC_stateupdate mScript;

    public void setAppContext(Context bdctx) {
        this.bdContext = bdctx;
    }

    public float getTime() {
        return t;
    }

    public float getDuration() {
        return _duration;
    }

    public String getStatusText() {
        return simulationStatus;
    }

    public String getDescription() {
        return DESCRIPTION;
    }

    public String getRuntimeDuration() {
        return ""+runtimeDuration;
    }

    public int getSimState() {
        return simstate;
    }

    protected void setStatusText(String statusText) {
        simulationStatus = statusText;
    }

    protected void appendStatusText(String extraText) {
        simulationStatus += extraText;
    }

    //*********** %% GLOBAL VARS %% **********//

    %JAVA ARRAY DECLARATIONS%

    %ALLOCATION DECLARATIONS%

    public void setup() {
        _duration = 1;
        mRS = RenderScript.create(bdContext);
        mScript = new ScriptC_stateupdate(mRS);

        %JAVA ARRAY INITIALISATIONS%

        %ALLOCATION INITIALISATIONS%

        %MEMORY BINDINGS%

        Log.d(LOGID, "Memory allocation and binding complete.");
    }

    public boolean isExternalStorageWritable() {
        String state = Environment.getExternalStorageState();
        if (Environment.MEDIA_MOUNTED.equals(state)) {
            return true;
        }
        return false;
    }

    private void writeToFile(float[][] monitor, String filename) {
        Log.d(LOGID, "Writing to file "+filename);
        if (isExternalStorageWritable()) {
            final int N = monitor.length;
            StringBuilder dataSB = new StringBuilder();
            for (int idx=0; idx<N; idx++) {
                float[] mon_idx = monitor[idx];
                for (double mi : mon_idx) {
                    dataSB.append(mi+" ");
                }
                dataSB.append("\n");
            }
            try {
                File sdCard = Environment.getExternalStorageDirectory();
                File dir = new File(sdCard.getAbsolutePath()+"/BrianDROIDout/"); //TODO: optional save path
                dir.mkdirs();
                File spikesFile = new File(dir, filename);
                FileOutputStream spikesStream = new FileOutputStream(spikesFile);
                spikesStream.write(dataSB.toString().getBytes()); // this might be inefficient
                spikesStream.close();
                Log.d(LOGID, "DONE!");
            } catch (Exception e) {
                Log.e(LOGID, "File write failed!");
                e.printStackTrace();
            }
        }
    }

    private void writeToFile(ArrayList<?>[] monitor, String filename) {
        if (isExternalStorageWritable()) {
            final int N = monitor.length;
            StringBuilder dataSB = new StringBuilder();
            for (int idx=0; idx<N; idx++) {
                ArrayList<Double> mon_idx = (ArrayList<Double>)monitor[idx];
                for (double mi : mon_idx) {
                    dataSB.append(mi+" ");
                }
                dataSB.append("\n");
            }
            try {
                File sdCard = Environment.getExternalStorageDirectory();
                File dir = new File(sdCard.getAbsolutePath()+"/BrianDROIDout/"); //TODO: optional save path
                dir.mkdirs();
                File spikesFile = new File(dir, filename);
                FileOutputStream spikesStream = new FileOutputStream(spikesFile);
                spikesStream.write(dataSB.toString().getBytes()); // this might be inefficient
                spikesStream.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    protected void onProgressUpdate(String... progress) {
        setStatusText("Running simulation: "+progress[0]+"/"+_duration);
    }

    @Override
    protected Void doInBackground(Void... ign) {
        run();
        return null;
    }

    //*********** MAIN LOOP *************
    public void run() {
        Log.d(LOGID, "Starting run code ...");
        simstate = 1;
        %JAVA IDX INITIALISATIONS%
        long sim_start = System.currentTimeMillis();
        for (t=0; t<_duration; t+=dt) {
            mScript.set_t(t);
            %KERNEL CALLS%
            publishProgress(""+t);
            mRS.finish();
        }
        runtimeDuration = System.currentTimeMillis()-sim_start;
        Log.d(LOGID, "DONE!");
        simstate = 2;

    }



}
