package com.openclaw.homeassistant;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * 线程池管理器
 * 统一管理后台任务执行，避免直接创建线程导致的内存泄漏
 */
public class ThreadPoolManager {
    
    private static volatile ThreadPoolManager instance;
    private final ExecutorService executor;
    
    private ThreadPoolManager() {
        int processors = Runtime.getRuntime().availableProcessors();
        int poolSize = Math.max(2, Math.min(processors, 4));
        executor = Executors.newFixedThreadPool(poolSize);
    }
    
    public static ThreadPoolManager getInstance() {
        if (instance == null) {
            synchronized (ThreadPoolManager.class) {
                if (instance == null) {
                    instance = new ThreadPoolManager();
                }
            }
        }
        return instance;
    }
    
    /**
     * 提交任务到线程池
     */
    public Future<?> submit(Runnable task) {
        return executor.submit(task);
    }
    
    /**
     * 在后台线程执行任务
     */
    public void execute(Runnable task) {
        executor.execute(task);
    }
    
    /**
     * 关闭线程池
     */
    public void shutdown() {
        executor.shutdown();
    }
    
    /**
     * 立即关闭线程池
     */
    public void shutdownNow() {
        executor.shutdownNow();
    }
}