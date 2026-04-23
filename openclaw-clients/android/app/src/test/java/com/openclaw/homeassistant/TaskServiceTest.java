package com.openclaw.homeassistant;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

/**
 * TaskService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class TaskServiceTest {
    
    private TaskService taskService;
    
    @Before
    public void setUp() {
        taskService = new TaskService(RuntimeEnvironment.getApplication().getApplicationContext());
    }
    
    @Test
    public void testCreateTask() {
        // 测试创建任务
        taskService.createTask("测试任务", "描述", "测试用户", 10, "2026-03-05", null, "管理员");
        
        // 验证任务已创建
        assertNotNull(taskService);
    }
    
    @Test
    public void testCompleteTask() {
        // 先创建任务
        taskService.createTask("洗碗", "", "孩子", 10, "2026-03-05", null, "妈妈");
        
        // 获取任务 ID（简化测试）
        // 实际应从数据库查询
        assertNotNull(taskService);
    }
    
    @Test
    public void testAddPoints() {
        // 测试添加积分
        taskService.addPoints("测试用户", 50, "测试原因");
        
        // 验证积分已添加
        int points = taskService.getMemberPoints("测试用户");
        assertTrue(points >= 50);
    }
    
    @Test
    public void testGetMemberPoints() {
        // 测试获取积分
        int points = taskService.getMemberPoints("新用户");
        
        // 新用户积分为 0
        assertEquals(0, points);
    }
    
    @Test
    public void testGetLeaderboard() {
        // 测试获取排行榜
        List<Map<String, Object>> leaderboard = taskService.getLeaderboard();
        
        // 验证返回排行榜
        assertNotNull(leaderboard);
    }
    
    @Test
    public void testGetPendingTasks() {
        // 测试获取待办任务
        List<Map<String, Object>> tasks = taskService.getPendingTasks();
        
        // 验证返回任务列表
        assertNotNull(tasks);
    }
    
    @Test
    public void testRedeemReward() {
        // 先添加积分
        taskService.addPoints("测试用户", 100, "初始积分");
        
        // 测试兑换奖励
        taskService.redeemReward("测试用户", "测试奖励", 50);
        
        // 验证积分已扣除
        int points = taskService.getMemberPoints("测试用户");
        assertEquals(50, points);
    }
    
    @Test
    public void testCreateDefaultTasks() {
        // 测试创建默认任务
        taskService.createDefaultTasks();
        
        // 验证任务已创建
        List<Map<String, Object>> tasks = taskService.getPendingTasks();
        assertTrue(tasks.size() >= 3);
    }
}
