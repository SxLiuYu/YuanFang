package com.openclaw.homeassistant;

import android.content.Context;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

import static org.junit.Assert.*;

/**
 * MemberService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class MemberServiceTest {

    private MemberService memberService;
    private Context context;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        context = RuntimeEnvironment.getApplication().getApplicationContext();
        memberService = new MemberService(context);
    }

    @Test
    public void testServiceNotNull() {
        assertNotNull("服务不应为空", memberService);
    }

    @Test
    public void testAddMember() {
        // 测试添加家庭成员
        long memberId = memberService.addMember(
            "测试用户",
            "son",
            "avatar_001"
        );

        assertTrue("成员ID应大于0", memberId > 0);
    }

    @Test
    public void testGetMembers() {
        // 测试获取家庭成员列表
        assertNotNull("成员列表不应为空", memberService.getMembers());
    }

    @Test
    public void testUpdateMember() {
        // 先添加一个成员
        long memberId = memberService.addMember(
            "原名称",
            "daughter",
            "avatar_002"
        );

        // 更新成员
        boolean result = memberService.updateMember(
            memberId,
            "新名称",
            "daughter",
            "avatar_003"
        );

        assertTrue("更新应成功", result);
    }

    @Test
    public void testDeleteMember() {
        // 先添加一个成员
        long memberId = memberService.addMember(
            "待删除成员",
            "other",
            "avatar_004"
        );

        // 删除成员
        boolean result = memberService.deleteMember(memberId);
        assertTrue("删除应成功", result);
    }

    @Test
    public void testGetMemberPoints() {
        // 测试获取成员积分
        long memberId = memberService.addMember(
            "积分测试",
            "son",
            "avatar_005"
        );

        int points = memberService.getMemberPoints(memberId);
        assertTrue("积分应大于等于0", points >= 0);
    }

    @Test
    public void testAddPoints() {
        // 先添加一个成员
        long memberId = memberService.addMember(
            "积分增加测试",
            "daughter",
            "avatar_006"
        );

        // 增加积分
        boolean result = memberService.addPoints(memberId, 10, "完成家务");
        assertTrue("增加积分应成功", result);
    }

    @Test
    public void testGetMemberRole() {
        // 测试获取成员角色
        assertNotNull("角色列表不应为空", memberService.getRoles());
    }
}