package com.github.wenweihu86.raft;

import java.io.File;

import org.omg.PortableInterceptor.Interceptor;

/**
 * Since TLA+ cannot handle real-world time logic. We use this trick class to handle it.
 * 
 * This class use some deterministic flag to control whether some events happen.
 * At now, this is usually companioned with some modifications on source codes.
 */
public class MDCBTimingHandler {
    public static boolean beginSnapshot = false;

    public static void scanSnapShotFlag() {
        int sid = Interceptor.sid;
        String filePath = "/home/fwhdzh/code/private-raft-java/fwh/raft-java-flag/snapshot-"+sid+".flag";
        while (true) {
            File file = new File(filePath);
            if (file.exists()) {
                System.out.println("File exists: " + filePath);
                file.delete();
                beginSnapshot = true;
            } else {
                System.out.println("File does not exist: " + filePath);
            }

            try {
                Thread.sleep(1000); // Sleep for 1 second
            } catch (InterruptedException e) {
                System.err.println("Thread was interrupted");
                Thread.currentThread().interrupt();
                break; // Exit loop if the thread is interrupted
            }
        }
    }


    public static void begin() {
        Thread scanSnapshotThread = new Thread() {
            @Override
			public void run() {
				scanSnapShotFlag();
			}
        };
        scanSnapshotThread.start();
    }
}
