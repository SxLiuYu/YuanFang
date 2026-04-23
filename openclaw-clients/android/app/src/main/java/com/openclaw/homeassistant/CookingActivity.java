package com.openclaw.homeassistant;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 做菜助手界面
 * 支持菜谱搜索、语音指导、计时器、采购清单
 */
public class CookingActivity extends AppCompatActivity implements TextToSpeech.OnInitListener {

    private static final String TAG = "CookingActivity";

    // UI 组件
    private EditText edtSearch;
    private Button btnSearch;
    private Button btnVoiceSearch;
    private RecyclerView recyclerRecipes;
    private TextView txtTimer;
    private Button btnStartTimer;
    private Button btnStopTimer;
    private TextView txtCurrentStep;
    private Button btnNextStep;
    private Button btnPrevStep;
    private Button btnRepeatStep;
    private Button btnAddToList;

    // 服务
    private TextToSpeech tts;
    private CountDownTimer countDownTimer;
    private SpeechRecognizer speechRecognizer;

    // 数据
    private List<Recipe> recipes = new ArrayList<>();
    private Recipe currentRecipe;
    private int currentStepIndex = 0;
    private long timerSeconds = 0;

    // 权限请求器
    private ActivityResultLauncher<String> permissionLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cooking);

        // 初始化 TTS
        tts = new TextToSpeech(this, this);

        // 初始化权限请求器
        permissionLauncher = registerForActivityResult(
            new ActivityResultContracts.RequestPermission(),
            isGranted -> {
                if (isGranted) {
                    startVoiceSearch();
                } else {
                    showToast("需要录音权限才能使用语音搜索");
                }
            });

        // 绑定 UI
        bindViews();

        // 设置按钮
        setupButtons();

        // 初始化语音识别
        setupVoiceSearch();
    }

    private void bindViews() {
        edtSearch = findViewById(R.id.edt_search);
        btnSearch = findViewById(R.id.btn_search);
        btnVoiceSearch = findViewById(R.id.btn_voice_search);
        recyclerRecipes = findViewById(R.id.recycler_recipes);
        txtTimer = findViewById(R.id.txt_timer);
        btnStartTimer = findViewById(R.id.btn_start_timer);
        btnStopTimer = findViewById(R.id.btn_stop_timer);
        txtCurrentStep = findViewById(R.id.txt_current_step);
        btnNextStep = findViewById(R.id.btn_next_step);
        btnPrevStep = findViewById(R.id.btn_prev_step);
        btnRepeatStep = findViewById(R.id.btn_repeat_step);
        btnAddToList = findViewById(R.id.btn_add_to_list);

        recyclerRecipes.setLayoutManager(new LinearLayoutManager(this));
    }

    private void setupButtons() {
        // 搜索菜谱
        btnSearch.setOnClickListener(v -> {
            String keyword = edtSearch.getText().toString().trim();
            if (!keyword.isEmpty()) {
                searchRecipes(keyword);
            }
        });

        // 语音搜索
        btnVoiceSearch.setOnClickListener(v -> {
            checkAndStartVoiceSearch();
        });

        // 计时器
        btnStartTimer.setOnClickListener(v -> startTimer());
        btnStopTimer.setOnClickListener(v -> stopTimer());

        // 步骤控制
        btnNextStep.setOnClickListener(v -> nextStep());
        btnPrevStep.setOnClickListener(v -> prevStep());
        btnRepeatStep.setOnClickListener(v -> repeatStep());

        // 添加到购物清单
        btnAddToList.setOnClickListener(v -> addToShoppingList());
    }

    /**
     * 搜索菜谱
     */
    private void searchRecipes(String keyword) {
        showToast("正在搜索: " + keyword);

        ThreadPoolManager.getInstance().execute(() -> {
            try {
                runOnUiThread(() -> {
                    recipes.clear();
                    recipes.add(new Recipe("红烧肉", "经典家常菜", 30, "中等"));
                    recipes.add(new Recipe("西红柿炒蛋", "简单快手菜", 10, "简单"));
                    recipes.add(new Recipe("宫保鸡丁", "川菜经典", 25, "中等"));
                    showToast("找到 " + recipes.size() + " 个菜谱");
                });
            } catch (Exception e) {
                Log.e(TAG, "搜索菜谱失败", e);
            }
        });
    }

    /**
     * 选择菜谱
     */
    public void selectRecipe(Recipe recipe) {
        currentRecipe = recipe;
        currentStepIndex = 0;
        loadRecipeSteps();
        speak("开始制作" + recipe.name + "，请准备好食材");
    }

    /**
     * 加载菜谱步骤
     */
    private void loadRecipeSteps() {
        if (currentRecipe != null) {
            txtCurrentStep.setText(currentRecipe.getStep(currentStepIndex));
        }
    }

    /**
     * 下一步
     */
    private void nextStep() {
        if (currentRecipe != null && currentStepIndex < currentRecipe.getStepCount() - 1) {
            currentStepIndex++;
            loadRecipeSteps();
            speak(currentRecipe.getStep(currentStepIndex));
        } else {
            speak("已完成所有步骤，祝您用餐愉快！");
        }
    }

    /**
     * 上一步
     */
    private void prevStep() {
        if (currentRecipe != null && currentStepIndex > 0) {
            currentStepIndex--;
            loadRecipeSteps();
            speak(currentRecipe.getStep(currentStepIndex));
        }
    }

    /**
     * 重复当前步骤
     */
    private void repeatStep() {
        if (currentRecipe != null) {
            speak(currentRecipe.getStep(currentStepIndex));
        }
    }

    /**
     * 开始计时器
     */
    private void startTimer() {
        // 默认 10 分钟
        timerSeconds = 10 * 60;

        countDownTimer = new CountDownTimer(timerSeconds * 1000, 1000) {
            @Override
            public void onTick(long millisUntilFinished) {
                long minutes = millisUntilFinished / 1000 / 60;
                long seconds = (millisUntilFinished / 1000) % 60;
                txtTimer.setText(String.format("%02d:%02d", minutes, seconds));
            }

            @Override
            public void onFinish() {
                txtTimer.setText("00:00");
                speak("计时结束！");
                showToast("计时结束！");
            }
        };

        countDownTimer.start();
        speak("计时开始，10分钟");
    }

    /**
     * 停止计时器
     */
    private void stopTimer() {
        if (countDownTimer != null) {
            countDownTimer.cancel();
            txtTimer.setText("00:00");
            speak("计时已停止");
        }
    }

    /**
     * 添加到购物清单
     */
    private void addToShoppingList() {
        if (currentRecipe != null) {
            // 添加食材到购物清单
            ShoppingService shoppingService = new ShoppingService(this);
            for (String ingredient : currentRecipe.ingredients) {
                shoppingService.addItem(ingredient, "食材", 1, "份", "我");
            }
            speak("已将食材添加到购物清单");
            showToast("已添加到购物清单");
        }
    }

    /**
     * 语音播报
     */
    private void speak(String text) {
        if (tts != null) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
        }
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            tts.setLanguage(Locale.CHINA);
            Log.d(TAG, "TTS 初始化成功");
        } else {
            Log.e(TAG, "TTS 初始化失败");
        }
    }

    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        if (countDownTimer != null) {
            countDownTimer.cancel();
        }
        if (speechRecognizer != null) {
            speechRecognizer.destroy();
        }
    }

    /**
     * 初始化语音识别
     */
    private void setupVoiceSearch() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            btnVoiceSearch.setEnabled(false);
            return;
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                showToast("🎤 请说出菜名...");
            }

            @Override
            public void onBeginningOfSpeech() {}

            @Override
            public void onEndOfSpeech() {}

            @Override
            public void onError(int error) {
                String errorMsg;
                switch (error) {
                    case SpeechRecognizer.ERROR_NO_MATCH:
                        errorMsg = "未识别到语音，请重试";
                        break;
                    case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                        errorMsg = "需要录音权限";
                        break;
                    default:
                        errorMsg = "语音识别错误";
                }
                showToast(errorMsg);
            }

            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String keyword = matches.get(0);
                    edtSearch.setText(keyword);
                    searchRecipes(keyword);
                }
            }

            @Override
            public void onPartialResults(Bundle partialResults) {}

            @Override
            public void onEvent(int eventType, Bundle params) {}

            @Override
            public void onRmsChanged(float rmsdB) {}

            @Override
            public void onBufferReceived(byte[] buffer) {}
        });
    }

    /**
     * 检查权限并启动语音搜索
     */
    private void checkAndStartVoiceSearch() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED) {
            startVoiceSearch();
        } else {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO);
        }
    }

    /**
     * 启动语音搜索
     */
    private void startVoiceSearch() {
        if (speechRecognizer == null) {
            showToast("语音识别不可用");
            return;
        }

        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "zh-CN");
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
        speechRecognizer.startListening(intent);
    }

    /**
     * 菜谱数据类
     */
    public static class Recipe {
        public String name;
        public String description;
        public int cookTime;
        public String difficulty;
        public List<String> ingredients = new ArrayList<>();
        public List<String> steps = new ArrayList<>();

        public Recipe(String name, String description, int cookTime, String difficulty) {
            this.name = name;
            this.description = description;
            this.cookTime = cookTime;
            this.difficulty = difficulty;

            // 模拟步骤
            steps.add("第一步：准备食材");
            steps.add("第二步：清洗处理");
            steps.add("第三步：热锅放油");
            steps.add("第四步：开始烹饪");
            steps.add("第五步：调味出锅");
        }

        public String getStep(int index) {
            if (index >= 0 && index < steps.size()) {
                return steps.get(index);
            }
            return "";
        }

        public int getStepCount() {
            return steps.size();
        }
    }
}