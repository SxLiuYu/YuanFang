package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 家庭成员管理服务
 * 支持多用户、权限管理、家庭成员邀请
 */
public class MemberService {
    
    private static final String TAG = "MemberService";
    private static final String PREFS_NAME = "family_members";
    
    private final Context context;
    private final SharedPreferences prefs;
    
    // 成员角色
    public enum Role {
        ADMIN,      // 管理员（完全权限）
        MEMBER,     // 普通成员（部分权限）
        CHILD,      // 儿童模式（受限权限）
        GUEST       // 访客（只读权限）
    }
    
    // 权限类型
    public enum Permission {
        READ_DEVICES,       // 查看设备
        CONTROL_DEVICES,    // 控制设备
        READ_FINANCE,       // 查看账本
        MANAGE_FINANCE,     // 管理账本
        READ_TASKS,         // 查看任务
        MANAGE_TASKS,       // 管理任务
        MANAGE_MEMBERS,     // 管理成员
        MANAGE_AUTOMATION   // 管理自动化
    }
    
    public interface MemberListener {
        void onMemberAdded(Member member);
        void onMemberRemoved(String memberId);
        void onMemberUpdated(Member member);
        void onCurrentMemberChanged(Member member);
    }
    
    private static MemberListener listener;
    private Member currentMember;
    
    public MemberService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        
        // 加载当前成员
        loadCurrentMember();
    }
    
    public static void setListener(MemberListener listener) {
        MemberService.listener = listener;
    }
    
    // ========== 成员管理 ==========
    
    /**
     * 添加家庭成员
     */
    public Member addMember(String name, String nickname, String avatar, Role role, String relation) {
        String memberId = generateId();
        
        Member member = new Member(memberId, name, nickname, avatar, role, relation);
        
        // 设置默认权限
        member.setPermissions(getDefaultPermissions(role));
        
        // 保存到本地
        saveMember(member);
        
        Log.d(TAG, "添加成员：" + member.nickname + " (" + member.role + ")");
        
        if (listener != null) {
            listener.onMemberAdded(member);
        }
        
        return member;
    }
    
    /**
     * 移除家庭成员
     */
    public void removeMember(String memberId) {
        String key = "member_" + memberId;
        if (prefs.contains(key)) {
            prefs.edit().remove(key).apply();
            Log.d(TAG, "移除成员：" + memberId);
            
            if (listener != null) {
                listener.onMemberRemoved(memberId);
            }
        }
    }
    
    /**
     * 更新成员信息
     */
    public void updateMember(Member member) {
        saveMember(member);
        Log.d(TAG, "更新成员：" + member.nickname);
        
        if (listener != null) {
            listener.onMemberUpdated(member);
        }
    }
    
    /**
     * 获取所有家庭成员
     */
    public List<Member> getAllMembers() {
        List<Member> members = new ArrayList<>();
        
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("member_")) {
                try {
                    JSONObject json = new JSONObject(entry.getValue().toString());
                    members.add(new Member(json));
                } catch (Exception e) {
                    Log.e(TAG, "解析成员失败", e);
                }
            }
        }
        
        return members;
    }
    
    /**
     * 获取指定成员
     */
    public Member getMember(String memberId) {
        String key = "member_" + memberId;
        String json = prefs.getString(key, null);
        
        if (json != null) {
            try {
                return new Member(new JSONObject(json));
            } catch (Exception e) {
                Log.e(TAG, "获取成员失败", e);
            }
        }
        
        return null;
    }
    
    /**
     * 切换当前成员
     */
    public void switchMember(String memberId) {
        Member member = getMember(memberId);
        if (member != null) {
            currentMember = member;
            prefs.edit().putString("current_member_id", memberId).apply();
            Log.d(TAG, "切换到成员：" + member.nickname);
            
            if (listener != null) {
                listener.onCurrentMemberChanged(member);
            }
        }
    }
    
    /**
     * 获取当前成员
     */
    public Member getCurrentMember() {
        return currentMember;
    }
    
    /**
     * 检查当前成员权限
     */
    public boolean hasPermission(Permission permission) {
        if (currentMember == null) {
            return false;
        }
        
        // 管理员拥有所有权限
        if (currentMember.role == Role.ADMIN) {
            return true;
        }
        
        return currentMember.permissions.contains(permission);
    }
    
    // ========== 权限管理 ==========
    
    /**
     * 更新成员权限
     */
    public void updatePermissions(String memberId, List<Permission> permissions) {
        Member member = getMember(memberId);
        if (member != null) {
            member.setPermissions(permissions);
            updateMember(member);
        }
    }
    
    /**
     * 获取角色默认权限
     */
    private List<Permission> getDefaultPermissions(Role role) {
        List<Permission> permissions = new ArrayList<>();
        
        switch (role) {
            case ADMIN:
                // 管理员拥有所有权限
                permissions.addAll(getAllPermissions());
                break;
                
            case MEMBER:
                // 普通成员：查看和控制设备、查看和记账、查看和管理自己的任务
                permissions.add(Permission.READ_DEVICES);
                permissions.add(Permission.CONTROL_DEVICES);
                permissions.add(Permission.READ_FINANCE);
                permissions.add(Permission.MANAGE_FINANCE);
                permissions.add(Permission.READ_TASKS);
                permissions.add(Permission.MANAGE_TASKS);
                break;
                
            case CHILD:
                // 儿童模式：查看设备、查看任务、完成自己的任务
                permissions.add(Permission.READ_DEVICES);
                permissions.add(Permission.READ_TASKS);
                permissions.add(Permission.MANAGE_TASKS);
                break;
                
            case GUEST:
                // 访客：只读权限
                permissions.add(Permission.READ_DEVICES);
                permissions.add(Permission.READ_TASKS);
                break;
        }
        
        return permissions;
    }
    
    private List<Permission> getAllPermissions() {
        List<Permission> all = new ArrayList<>();
        all.add(Permission.READ_DEVICES);
        all.add(Permission.CONTROL_DEVICES);
        all.add(Permission.READ_FINANCE);
        all.add(Permission.MANAGE_FINANCE);
        all.add(Permission.READ_TASKS);
        all.add(Permission.MANAGE_TASKS);
        all.add(Permission.MANAGE_MEMBERS);
        all.add(Permission.MANAGE_AUTOMATION);
        return all;
    }
    
    // ========== 成员邀请 ==========
    
    /**
     * 生成邀请码
     */
    public String generateInviteCode() {
        // 生成 6 位邀请码
        String inviteCode = String.format("%06d", (int)(Math.random() * 1000000));
        
        // 保存邀请码（5 分钟有效）
        prefs.edit()
            .putString("invite_code", inviteCode)
            .putLong("invite_code_time", System.currentTimeMillis())
            .apply();
        
        Log.d(TAG, "生成邀请码：" + inviteCode);
        return inviteCode;
    }
    
    /**
     * 验证邀请码
     */
    public boolean verifyInviteCode(String code) {
        String savedCode = prefs.getString("invite_code", "");
        long codeTime = prefs.getLong("invite_code_time", 0);
        
        // 检查是否过期（5 分钟）
        if (System.currentTimeMillis() - codeTime > 5 * 60 * 1000) {
            return false;
        }
        
        return code.equals(savedCode);
    }
    
    // ========== 家庭统计 ==========
    
    /**
     * 获取家庭统计信息
     */
    public Map<String, Object> getFamilyStats() {
        Map<String, Object> stats = new HashMap<>();
        
        List<Member> members = getAllMembers();
        
        stats.put("total_members", members.size());
        stats.put("admin_count", countByRole(members, Role.ADMIN));
        stats.put("member_count", countByRole(members, Role.MEMBER));
        stats.put("child_count", countByRole(members, Role.CHILD));
        stats.put("guest_count", countByRole(members, Role.GUEST));
        
        return stats;
    }
    
    private int countByRole(List<Member> members, Role role) {
        int count = 0;
        for (Member member : members) {
            if (member.role == role) {
                count++;
            }
        }
        return count;
    }
    
    // ========== 工具方法 ==========
    
    private void saveMember(Member member) {
        String key = "member_" + member.id;
        prefs.edit().putString(key, member.toJson().toString()).apply();
    }
    
    private void loadCurrentMember() {
        String memberId = prefs.getString("current_member_id", null);
        if (memberId != null) {
            currentMember = getMember(memberId);
        }
    }
    
    private String generateId() {
        return String.valueOf(System.currentTimeMillis());
    }
    
    // ========== 成员类 ==========
    
    public static class Member {
        public String id;
        public String name;
        public String nickname;
        public String avatar;
        public Role role;
        public String relation;  // 与户主关系：本人、配偶、子女、父母等
        public List<Permission> permissions;
        public long joinedAt;
        public long lastActiveAt;
        
        public Member(String id, String name, String nickname, String avatar, Role role, String relation) {
            this.id = id;
            this.name = name;
            this.nickname = nickname;
            this.avatar = avatar;
            this.role = role;
            this.relation = relation;
            this.joinedAt = System.currentTimeMillis();
            this.lastActiveAt = System.currentTimeMillis();
            this.permissions = new ArrayList<>();
        }
        
        public Member(JSONObject json) throws Exception {
            this.id = json.getString("id");
            this.name = json.getString("name");
            this.nickname = json.optString("nickname", name);
            this.avatar = json.optString("avatar", "");
            this.role = Role.valueOf(json.getString("role"));
            this.relation = json.optString("relation", "");
            this.joinedAt = json.optLong("joined_at", System.currentTimeMillis());
            this.lastActiveAt = json.optLong("last_active_at", System.currentTimeMillis());
            
            this.permissions = new ArrayList<>();
            JSONArray perms = json.optJSONArray("permissions");
            if (perms != null) {
                for (int i = 0; i < perms.length(); i++) {
                    permissions.add(Permission.valueOf(perms.getString(i)));
                }
            }
        }
        
        public JSONObject toJson() {
            try {
                JSONObject json = new JSONObject();
                json.put("id", id);
                json.put("name", name);
                json.put("nickname", nickname);
                json.put("avatar", avatar);
                json.put("role", role.name());
                json.put("relation", relation);
                json.put("joined_at", joinedAt);
                json.put("last_active_at", lastActiveAt);
                
                JSONArray perms = new JSONArray();
                for (Permission perm : permissions) {
                    perms.put(perm.name());
                }
                json.put("permissions", perms);
                
                return json;
            } catch (Exception e) {
                Log.e(TAG, "转换为 JSON 失败", e);
                return new JSONObject();
            }
        }
        
        public void setPermissions(List<Permission> permissions) {
            this.permissions = permissions;
        }
        
        public boolean hasPermission(Permission permission) {
            return permissions.contains(permission);
        }
        
        public void updateActiveTime() {
            this.lastActiveAt = System.currentTimeMillis();
        }
    }
}
