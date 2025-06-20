import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> loginUser(String email, String password) async {
  final url = Uri.parse('http://127.0.0.1:8000/api/users/login/');

  final headers = {"Content-Type": "application/json"};
  final body = jsonEncode({
    "email": email,
    "password": password,
  });

  try {
    final response = await http.post(url, headers: headers, body: body);

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      print("✅ Giriş başarılı: $data");

      final token = data['access'];
      print("🔐 Access token: $token");
    } else {
      print("❌ Giriş başarısız: ${response.statusCode} - ${response.body}");
    }
  } catch (e) {
    print("⚠️ Hata oluştu: $e");
  }
}
