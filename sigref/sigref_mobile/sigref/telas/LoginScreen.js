import React, { useState } from 'react';
import { 
  View, 
  TextInput, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  Modal, 
  TouchableOpacity, 
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Dimensions
} from 'react-native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import gre from '../assets/CARD DA GRE.png';
import sigref from '../assets/SIGREF.png';
// const API_BASE_URL = 'http://127.0.0.1:8000'; //para pc
const API_BASE_URL = 'http://10.0.2.2:8000'; //para emulador android
//const API_BASE_URL = 'https://grefloresta.com.br';  URL do servidor remoto
const { width, height } = Dimensions.get('window');

const LoginScreen = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      setErrorMessage('Preencha todos os campos.');
      setShowErrorModal(true);
      return;
    }

    setLoading(true);
    
    try {
      const netInfoState = await NetInfo.fetch();
      if (!netInfoState.isConnected) {
        setErrorMessage('Você está offline. Conecte-se à internet para fazer login.');
        setShowErrorModal(true);
        setLoading(false);
        return;
      }

      const response = await axios.post(`${API_BASE_URL}/api/login/`, { 
        username,
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (response.data.success) {
        const userData = {
          token: response.data.token,
          fullName: response.data.full_name,
          userType: response.data.user_type,
          userTypeDisplay: response.data.user_type_display,
          accessLevel: response.data.access_level,
          email: response.data.email,
          username: response.data.username,
          celular: response.data.celular,
          cpf: response.data.cpf,
          escolas: response.data.escolas || [],
          setor: response.data.setor || null,
        };

        await AsyncStorage.setItem('userData', JSON.stringify(userData));
        navigation.replace('Home', { userData });
      } else {
        setErrorMessage(response.data.message || 'Erro desconhecido na resposta do servidor.');
        setShowErrorModal(true);
      }
    } catch (error) {
      console.error("Erro na requisição de login:", error);
      if (error.response) {
        setErrorMessage(error.response.data.message || 'Erro na resposta do servidor.');
      } else if (error.request) {
        setErrorMessage('Não foi possível conectar ao servidor. Verifique sua conexão ou o endereço do servidor.');
      } else {
        setErrorMessage('Ocorreu um erro inesperado ao tentar fazer login.');
      }
      setShowErrorModal(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logos */}
        <View style={styles.logoContainer}>
          <Image 
            source={sigref}  
            style={styles.sigrefLogo}
            resizeMode="stretch"
          />
         
        </View>
        
        <Text style={styles.title}>Sistema Integrado de Gerência Regional de Educação de Floresta</Text>
        
        {/* Formulário de Login */}
        <View style={styles.formContainer}>
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Usuário</Text>
            <TextInput
              style={styles.input}
              placeholder="Digite seu usuário"
              placeholderTextColor="#999"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>
          
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Senha</Text>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                placeholder="Digite sua senha"
                placeholderTextColor="#999"
                secureTextEntry={!showPassword}
                value={password}
                onChangeText={setPassword}
              />
              <TouchableOpacity 
                style={styles.showPasswordButton}
                onPress={() => setShowPassword(!showPassword)}
              >
                <Text style={styles.showPasswordText}>
                  {showPassword ? 'Ocultar' : 'Mostrar'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
          
          {/* Botão de Login */}
          <TouchableOpacity 
            style={styles.loginButton}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.loginButtonText}>Entrar</Text>
            )}
          </TouchableOpacity>
          
          {/* Esqueceu a senha? */}
          <TouchableOpacity style={styles.forgotPassword}>
            <Text style={styles.forgotPasswordText}>Esqueceu sua senha?</Text>
          </TouchableOpacity>
        </View>
        
        {/* Rodapé */}
        <View style={styles.footer}>
           <Image 
            source={gre} 
            style={styles.greLogo}
            resizeMode="stretch"
          />
          <Text style={styles.footerText}>© 2025 SIGREF - GRE Floresta</Text>
          <Text style={styles.footerText}>Versão 1.0.0</Text>
        </View>
      </ScrollView>
      
      {/* Modal de Erro Personalizado */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={showErrorModal}
        onRequestClose={() => {
          setShowErrorModal(!showErrorModal);
        }}
      >
        <View style={styles.centeredView}>
          <View style={styles.modalView}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Erro no Login</Text>
            </View>
            <View style={styles.modalBody}>
             
              <Text style={styles.modalText}>{errorMessage}</Text>
            </View>
            <TouchableOpacity
              style={styles.buttonClose}
              onPress={() => setShowErrorModal(false)}
            >
              <Text style={styles.textStyle}>Entendido</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fc',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  sigrefLogo: {
    width: width * 0.35,
    height: height * 0.15,
    marginBottom: -25,
  },
  greLogo: {
    width: width * 0.4,
    height: 80,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 30,
    color: '#2d3748',
  },
  formContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    marginBottom: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
    color: '#4a5568',
  },
  input: {
    height: 50,
    borderColor: '#e2e8f0',
    borderWidth: 1,
    paddingHorizontal: 15,
    borderRadius: 10,
    backgroundColor: '#f8fafc',
    fontSize: 16,
    color: '#1a202c',
  },
  passwordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderColor: '#e2e8f0',
    borderWidth: 1,
    borderRadius: 10,
    backgroundColor: '#f8fafc',
  },
  passwordInput: {
    flex: 1,
    height: 50,
    paddingHorizontal: 15,
    borderWidth: 0,
  },
  showPasswordButton: {
    paddingHorizontal: 15,
    height: 50,
    justifyContent: 'center',
  },
  showPasswordText: {
    color: '#4e73df',
    fontWeight: '600',
  },
  loginButton: {
    backgroundColor: '#4e73df',
    borderRadius: 10,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#4e73df',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  loginButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 18,
  },
  forgotPassword: {
    alignSelf: 'center',
    marginTop: 20,
  },
  forgotPasswordText: {
    color: '#4e73df',
    fontWeight: '600',
  },
  footer: {
    marginTop: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#718096',
    marginBottom: 5,
  },
  // Estilos para o Modal
  centeredView: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalView: {
    margin: 20,
    backgroundColor: 'white',
    borderRadius: 20,
    overflow: 'hidden',
    width: '90%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  modalHeader: {
    backgroundColor: '#4e73df',
    padding: 15,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
  },
  modalBody: {
    padding: 25,
    alignItems: 'center',
  },
  modalLogo: {
    width: 80,
    height: 40,
    marginBottom: 20,
  },
  modalText: {
    marginBottom: 15,
    textAlign: 'center',
    fontSize: 16,
    color: '#555',
    lineHeight: 24,
  },
  buttonClose: {
    backgroundColor: '#4e73df',
    borderRadius: 10,
    padding: 12,
    elevation: 2,
    margin: 20,
    alignItems: 'center',
  },
  textStyle: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default LoginScreen;