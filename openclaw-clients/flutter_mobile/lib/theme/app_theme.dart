import 'package:flutter/material.dart';

class AppColors {
  static const Color primaryLight = Color(0xFF4F46E5);
  static const Color primaryDark = Color(0xFF818CF8);
  
  static const Color secondaryLight = Color(0xFF10B981);
  static const Color secondaryDark = Color(0xFF34D399);
  
  static const Color accentLight = Color(0xFFF59E0B);
  static const Color accentDark = Color(0xFFFBBF24);
  
  static const Color errorLight = Color(0xFFEF4444);
  static const Color errorDark = Color(0xFFF87171);
  
  static const Color successLight = Color(0xFF22C55E);
  static const Color successDark = Color(0xFF4ADE80);
  
  static const Color warningLight = Color(0xFFF59E0B);
  static const Color warningDark = Color(0xFFFBBF24);
  
  static const Color infoLight = Color(0xFF3B82F6);
  static const Color infoDark = Color(0xFF60A5FA);

  static const Color backgroundLight = Color(0xFFFAFAFA);
  static const Color backgroundDark = Color(0xFF111827);
  
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color surfaceDark = Color(0xFF1F2937);
  
  static const Color cardLight = Color(0xFFFFFFFF);
  static const Color cardDark = Color(0xFF1F2937);

  static const Map<String, Color> categoryColors = {
    'food': Color(0xFFFF6B6B),
    'transport': Color(0xFF4ECDC4),
    'shopping': Color(0xFFFFE66D),
    'entertainment': Color(0xFF95E1D3),
    'health': Color(0xFF6C5CE7),
    'education': Color(0xFFA8E6CF),
    'other': Color(0xFFDDA0DD),
  };

  static const List<Color> chartColors = [
    Color(0xFF4F46E5),
    Color(0xFF10B981),
    Color(0xFFF59E0B),
    Color(0xFFEF4444),
    Color(0xFF8B5CF6),
    Color(0xFF06B6D4),
    Color(0xFFEC4899),
    Color(0xFF14B8A6),
  ];
}

class AppTextStyles {
  static TextStyle get heading1 => const TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.bold,
        letterSpacing: -0.5,
      );
  
  static TextStyle get heading2 => const TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.bold,
        letterSpacing: -0.3,
      );
  
  static TextStyle get heading3 => const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.2,
      );
  
  static TextStyle get heading4 => const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w600,
      );
  
  static TextStyle get subtitle1 => const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w500,
      );
  
  static TextStyle get subtitle2 => const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w500,
      );
  
  static TextStyle get body1 => const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.normal,
      );
  
  static TextStyle get body2 => const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.normal,
      );
  
  static TextStyle get caption => const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.normal,
      );
  
  static TextStyle get overline => const TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w500,
        letterSpacing: 1.5,
      );
  
  static TextStyle get button => const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      );
  
  static TextStyle get label => const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.5,
      );
}

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: ColorScheme.light(
        primary: AppColors.primaryLight,
        secondary: AppColors.secondaryLight,
        error: AppColors.errorLight,
        surface: AppColors.surfaceLight,
      ),
      scaffoldBackgroundColor: AppColors.backgroundLight,
      cardColor: AppColors.cardLight,
      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: true,
        backgroundColor: AppColors.surfaceLight,
        foregroundColor: Colors.black87,
        titleTextStyle: AppTextStyles.heading4.copyWith(color: Colors.black87),
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      cardTheme: CardTheme(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        color: AppColors.cardLight,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: AppTextStyles.button,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          textStyle: AppTextStyles.button,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: AppTextStyles.button,
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[100],
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.primaryLight, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.errorLight, width: 1),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        labelStyle: AppTextStyles.subtitle2.copyWith(color: Colors.grey[600]),
        hintStyle: AppTextStyles.subtitle2.copyWith(color: Colors.grey[400]),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: AppColors.surfaceLight,
        selectedItemColor: AppColors.primaryLight,
        unselectedItemColor: Colors.grey[500],
        type: BottomNavigationBarType.fixed,
        elevation: 8,
        selectedLabelStyle: AppTextStyles.label,
        unselectedLabelStyle: AppTextStyles.label,
      ),
      tabBarTheme: TabBarTheme(
        labelColor: AppColors.primaryLight,
        unselectedLabelColor: Colors.grey[600],
        labelStyle: AppTextStyles.subtitle2,
        unselectedLabelStyle: AppTextStyles.body2,
        indicator: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: AppColors.primaryLight,
              width: 2,
            ),
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: Colors.grey[100],
        selectedColor: AppColors.primaryLight.withOpacity(0.2),
        disabledColor: Colors.grey[300],
        labelStyle: AppTextStyles.label,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dialogTheme: DialogTheme(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        titleTextStyle: AppTextStyles.heading4,
        contentTextStyle: AppTextStyles.body1,
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        contentTextStyle: AppTextStyles.body2.copyWith(color: Colors.white),
      ),
      dividerTheme: DividerThemeData(
        color: Colors.grey[200],
        thickness: 1,
        space: 1,
      ),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      textTheme: TextTheme(
        displayLarge: AppTextStyles.heading1,
        displayMedium: AppTextStyles.heading2,
        displaySmall: AppTextStyles.heading3,
        headlineLarge: AppTextStyles.heading1,
        headlineMedium: AppTextStyles.heading2,
        headlineSmall: AppTextStyles.heading3,
        titleLarge: AppTextStyles.heading4,
        titleMedium: AppTextStyles.subtitle1,
        titleSmall: AppTextStyles.subtitle2,
        bodyLarge: AppTextStyles.body1,
        bodyMedium: AppTextStyles.body2,
        bodySmall: AppTextStyles.caption,
        labelLarge: AppTextStyles.button,
        labelMedium: AppTextStyles.label,
        labelSmall: AppTextStyles.overline,
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.dark(
        primary: AppColors.primaryDark,
        secondary: AppColors.secondaryDark,
        error: AppColors.errorDark,
        surface: AppColors.surfaceDark,
      ),
      scaffoldBackgroundColor: AppColors.backgroundDark,
      cardColor: AppColors.cardDark,
      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: true,
        backgroundColor: AppColors.surfaceDark,
        foregroundColor: Colors.white,
        titleTextStyle: AppTextStyles.heading4.copyWith(color: Colors.white),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      cardTheme: CardTheme(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        color: AppColors.cardDark,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: AppTextStyles.button,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          textStyle: AppTextStyles.button,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: AppTextStyles.button,
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[800],
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.primaryDark, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.errorDark, width: 1),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        labelStyle: AppTextStyles.subtitle2.copyWith(color: Colors.grey[400]),
        hintStyle: AppTextStyles.subtitle2.copyWith(color: Colors.grey[500]),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: AppColors.surfaceDark,
        selectedItemColor: AppColors.primaryDark,
        unselectedItemColor: Colors.grey[500],
        type: BottomNavigationBarType.fixed,
        elevation: 8,
        selectedLabelStyle: AppTextStyles.label,
        unselectedLabelStyle: AppTextStyles.label,
      ),
      tabBarTheme: TabBarTheme(
        labelColor: AppColors.primaryDark,
        unselectedLabelColor: Colors.grey[400],
        labelStyle: AppTextStyles.subtitle2,
        unselectedLabelStyle: AppTextStyles.body2,
        indicator: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: AppColors.primaryDark,
              width: 2,
            ),
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: Colors.grey[800],
        selectedColor: AppColors.primaryDark.withOpacity(0.3),
        disabledColor: Colors.grey[700],
        labelStyle: AppTextStyles.label,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dialogTheme: DialogTheme(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        backgroundColor: AppColors.surfaceDark,
        titleTextStyle: AppTextStyles.heading4.copyWith(color: Colors.white),
        contentTextStyle: AppTextStyles.body1.copyWith(color: Colors.grey[300]),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        contentTextStyle: AppTextStyles.body2.copyWith(color: Colors.white),
      ),
      dividerTheme: DividerThemeData(
        color: Colors.grey[700],
        thickness: 1,
        space: 1,
      ),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      textTheme: TextTheme(
        displayLarge: AppTextStyles.heading1.copyWith(color: Colors.white),
        displayMedium: AppTextStyles.heading2.copyWith(color: Colors.white),
        displaySmall: AppTextStyles.heading3.copyWith(color: Colors.white),
        headlineLarge: AppTextStyles.heading1.copyWith(color: Colors.white),
        headlineMedium: AppTextStyles.heading2.copyWith(color: Colors.white),
        headlineSmall: AppTextStyles.heading3.copyWith(color: Colors.white),
        titleLarge: AppTextStyles.heading4.copyWith(color: Colors.white),
        titleMedium: AppTextStyles.subtitle1.copyWith(color: Colors.white),
        titleSmall: AppTextStyles.subtitle2.copyWith(color: Colors.grey[300]),
        bodyLarge: AppTextStyles.body1.copyWith(color: Colors.white),
        bodyMedium: AppTextStyles.body2.copyWith(color: Colors.grey[300]),
        bodySmall: AppTextStyles.caption.copyWith(color: Colors.grey[400]),
        labelLarge: AppTextStyles.button.copyWith(color: Colors.white),
        labelMedium: AppTextStyles.label.copyWith(color: Colors.grey[300]),
        labelSmall: AppTextStyles.overline.copyWith(color: Colors.grey[400]),
      ),
    );
  }

  static ThemeData getTheme({required bool isDark}) {
    return isDark ? darkTheme : lightTheme;
  }
}

extension ThemeExtensions on BuildContext {
  ThemeData get theme => Theme.of(this);
  TextTheme get textTheme => Theme.of(this).textTheme;
  ColorScheme get colors => Theme.of(this).colorScheme;
  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;
  
  TextStyle get heading1 => Theme.of(this).textTheme.displayLarge!;
  TextStyle get heading2 => Theme.of(this).textTheme.displayMedium!;
  TextStyle get heading3 => Theme.of(this).textTheme.displaySmall!;
  TextStyle get bodyText => Theme.of(this).textTheme.bodyMedium!;
  TextStyle get captionText => Theme.of(this).textTheme.bodySmall!;
}