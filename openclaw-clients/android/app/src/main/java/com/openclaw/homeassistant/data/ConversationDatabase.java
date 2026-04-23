package com.openclaw.homeassistant.data;

import android.content.Context;

import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;

@Database(
    entities = {MessageEntity.class, ChatSessionEntity.class},
    version = 1,
    exportSchema = false
)
public abstract class ConversationDatabase extends RoomDatabase {
    
    private static volatile ConversationDatabase INSTANCE;
    private static final String DATABASE_NAME = "conversation_db";
    
    public abstract MessageDao messageDao();
    
    public static ConversationDatabase getInstance(Context context) {
        if (INSTANCE == null) {
            synchronized (ConversationDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = Room.databaseBuilder(
                        context.getApplicationContext(),
                        ConversationDatabase.class,
                        DATABASE_NAME
                    )
                    .fallbackToDestructiveMigration()
                    .build();
                }
            }
        }
        return INSTANCE;
    }
    
    public static void destroyInstance() {
        INSTANCE = null;
    }
}