import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:openclaw_home_assistant/core/voice/voice_service.dart';

// Generate mocks
@GenerateMocks([stt.SpeechToText])
void main() {
  group('VoiceService', () {
    late VoiceService voiceService;
    late MockSpeechToText mockSpeech;

    setUp(() {
      voiceService = VoiceService._internal();
      mockSpeech = MockSpeechToText();
      
      // Inject mock
      voiceService._speech = mockSpeech;
    });

    test('initialize calls speech.initialize', () async {
      when(mockSpeech.initialize(
        onError: anyNamed('onError'),
        onStatus: anyNamed('onStatus'),
      )).thenAnswer((_) async => true);

      await voiceService.initialize();

      verify(mockSpeech.initialize(
        onError: anyNamed('onError'),
        onStatus: anyNamed('onStatus'),
      )).called(1);
    });

    test('startListening returns false when speech not available', () async {
      when(mockSpeech.isAvailable).thenReturn(false);
      
      final result = await voiceService.startListening();
      
      expect(result, false);
    });

    test('startListening calls speech.listen when available', () async {
      when(mockSpeech.isAvailable).thenReturn(true);
      when(mockSpeech.listen(
        onResult: anyNamed('onResult'),
        localeId: anyNamed('localeId'),
        listenFor: anyNamed('listenFor'),
        pauseFor: anyNamed('pauseFor'),
        partialResults: anyNamed('partialResults'),
        onSoundLevelChange: anyNamed('onSoundLevelChange'),
      )).thenAnswer((_) async => null);

      final result = await voiceService.startListening();
      
      expect(result, true);
      verify(mockSpeech.listen(
        onResult: anyNamed('onResult'),
        localeId: 'zh_CN',
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 2),
        partialResults: true,
        onSoundLevelChange: anyNamed('onSoundLevelChange'),
      )).called(1);
    });
  });
}