import React, { useState } from 'react';
import { View, TextInput, Button, Text, StyleSheet, ActivityIndicator, Modal, TouchableOpacity } from 'react-native'; // Adicionado Modal e TouchableOpacity
import axios from 'axios';

const LoginScreen = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false); // Estado para controlar a visibilidade do modal
  const [errorMessage, setErrorMessage] = useState(''); // Estado para armazenar a mensagem de erro

  const handleLogin = async () => {
    if (!username || !password) {
      setErrorMessage('Preencha todos os campos.'); // Define a mensagem de erro
      setShowErrorModal(true); // Mostra o modal
      return;
    }

    setLoading(true);
    
    try {
      // Mantenha o endereço IP correto para seu servidor Django
      // Ex: 'http://10.0.2.2:8000/api/login/' para emulador Android
      // Ex: 'http://SEU_IP_DA_MAQUINA:8000/api/login/' para dispositivo físico
      const response = await axios.post('http://127.0.0.1:8000/api/login/', { 
        username,
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      // Este bloco é executado se a API retornar um status 2xx (ex: 200 OK)
      if (response.data.success) {
        const userData = {
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

        navigation.replace('Home', { userData });
      } else {
        // Este bloco é executado se a API retornar um status 2xx, mas com success: false
        setErrorMessage(response.data.message || 'Erro desconhecido na resposta do servidor.');
        setShowErrorModal(true);
      }
    } catch (error) {
      // Este bloco é executado se a API retornar um status de erro (4xx, 5xx) ou se houver um problema de rede
      console.error("Erro na requisição de login:", error);
      if (error.response) {
        // O servidor respondeu com um status de erro (ex: 400, 401, 403, 500)
        setErrorMessage(error.response.data.message || 'Erro na resposta do servidor.');
      } else if (error.request) {
        // A requisição foi feita, mas nenhuma resposta foi recebida (problema de rede, servidor offline)
        setErrorMessage('Não foi possível conectar ao servidor. Verifique sua conexão ou o endereço do servidor.');
      } else {
        // Algo aconteceu na configuração da requisição que disparou um erro
        setErrorMessage('Ocorreu um erro inesperado ao tentar fazer login.');
      }
      setShowErrorModal(true); // Mostra o modal de erro
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sigref App</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Usuário"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Senha"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      
      {loading ? (
        <ActivityIndicator size="large" color="#0000ff" />
      ) : (
        <Button title="Entrar" onPress={handleLogin} />
      )}

      {/* Modal de Erro Personalizado */}
      <Modal
        animationType="fade" // Animação ao aparecer/desaparecer
        transparent={true} // Torna o fundo transparente para ver o conteúdo por trás
        visible={showErrorModal} // Controla a visibilidade com o estado
        onRequestClose={() => { // Para Android, permite fechar com o botão de voltar
          setShowErrorModal(!showErrorModal);
        }}
      >
        <View style={styles.centeredView}>
          <View style={styles.modalView}>
            <Text style={styles.modalTitle}>Erro</Text>
            <Text style={styles.modalText}>{errorMessage}</Text>
            <TouchableOpacity
              style={styles.buttonClose}
              onPress={() => setShowErrorModal(false)} // Esconde o modal ao clicar no botão
            >
              <Text style={styles.textStyle}>Fechar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5'
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30
  },
  input: {
    height: 50,
    borderColor: '#ccc',
    borderWidth: 1,
    marginBottom: 15,
    padding: 15,
    borderRadius: 5,
    backgroundColor: '#fff'
  },
  // Estilos para o Modal
  centeredView: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)', // Fundo semi-transparente
  },
  modalView: {
    margin: 20,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 35,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  modalText: {
    marginBottom: 15,
    textAlign: 'center',
    fontSize: 16,
    color: '#555',
  },
  buttonClose: {
    backgroundColor: '#2196F3',
    borderRadius: 10,
    padding: 10,
    elevation: 2,
    marginTop: 10,
  },
  textStyle: {
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default LoginScreen;
