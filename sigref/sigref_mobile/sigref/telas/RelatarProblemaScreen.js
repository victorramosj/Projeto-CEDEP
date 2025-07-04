// RelatarProblemaScreen.js
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Alert,
  Platform, // Para verificar a plataforma e ajustar o ImagePicker
  Image, // Para exibir a imagem selecionada
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker'; // Ou 'react-native-image-picker' se não usar Expo

// URL base da sua API Django (ajuste conforme necessário)
const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

const RelatarProblemaScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, userData } = route.params;

  const [descricao, setDescricao] = useState('');
  const [setorId, setSetorId] = useState(''); // Pode ser um TextInput ou Picker para selecionar
  const [loading, setLoading] = useState(false);
  const [image, setImage] = useState(null); // Para armazenar a URI da imagem selecionada
  const [setoresDisponiveis, setSetoresDisponiveis] = useState([]); // Para um futuro Picker de setores

  useEffect(() => {
    // Solicitar permissão de câmera e biblioteca de mídia ao montar o componente
    (async () => {
      if (Platform.OS !== 'web') {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permissão necessária', 'Desculpe, precisamos de permissões da galeria para isso funcionar!');
        }
        const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
        if (cameraStatus !== 'granted') {
          Alert.alert('Permissão necessária', 'Desculpe, precisamos de permissões da câmera para isso funcionar!');
        }
      }
    })();
    // TODO: Se você quiser um Picker de Setores, buscar os setores da API aqui
    // Ex: axios.get(`${API_BASE_URL}/api/setores/`).then(response => setSetoresDisponiveis(response.data));
  }, []);

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.5,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    let result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.5,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const handleSubmit = async () => {
    if (!descricao.trim()) {
      Alert.alert('Erro', 'Por favor, descreva o problema.');
      return;
    }

    setLoading(true);

    try {
      const token = userData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Faça login novamente.');
        navigation.replace('Login');
        return;
      }

      const formData = new FormData();
      formData.append('escola', escolaId);
      formData.append('descricao', descricao);
      if (setorId) {
        formData.append('setor', setorId); // Adicione se houver seleção de setor
      }

      if (image) {
        // Obter o nome do arquivo da URI
        const filename = image.split('/').pop();
        // Inferir o tipo do arquivo
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : `image`;

        formData.append('anexo', {
          uri: image,
          name: filename,
          type: type,
        });
      }

      const response = await axios.post(`${API_BASE_URL}/api/problemas-usuario/`, formData, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'multipart/form-data', // Essencial para FormData com arquivos
        },
      });

      if (response.status === 201) { // 201 Created é o status de sucesso para POST
        Alert.alert('Sucesso', 'Problema relatado com sucesso!');
        navigation.goBack(); // Volta para a tela anterior (SchoolDashboardScreen)
      } else {
        Alert.alert('Erro', `Falha ao relatar problema: ${response.data.detail || JSON.stringify(response.data)}`);
      }
    } catch (error) {
      console.error('Erro ao enviar problema:', error.response?.data || error.message);
      Alert.alert('Erro', 'Não foi possível relatar o problema. Verifique sua conexão ou tente novamente. Detalhes: ' + (error.response?.data ? JSON.stringify(error.response.data) : error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>Relatar Novo Problema</Text>

      <Text style={styles.label}>Escola:</Text>
      <TextInput
        style={styles.readOnlyInput}
        value={escolaId.toString()} // Exibe o ID da escola, é read-only
        editable={false}
      />
      {/* Se você tiver uma forma de mostrar o nome da escola, seria melhor */}
      {/* Ex: <Text style={styles.label}>Escola: {userData?.escolaNome}</Text> */}

      <Text style={styles.label}>Descrição do Problema:</Text>
      <TextInput
        style={styles.textArea}
        placeholder="Descreva o problema em detalhes..."
        multiline
        numberOfLines={5}
        value={descricao}
        onChangeText={setDescricao}
      />

      {/* Exemplo de Picker de Setor - requer uma biblioteca ou Picker nativo */}
      {/* Por enquanto, um TextInput simples para testar */}
      <Text style={styles.label}>ID do Setor (Opcional):</Text>
      <TextInput
        style={styles.input}
        placeholder="Ex: 1, 2, etc. (se souber)"
        keyboardType="numeric"
        value={setorId}
        onChangeText={setSetorId}
      />

      <View style={styles.imagePickerContainer}>
        <TouchableOpacity style={styles.imagePickerButton} onPress={pickImage}>
          <Text style={styles.imagePickerButtonText}>Escolher Imagem</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.imagePickerButton} onPress={takePhoto}>
          <Text style={styles.imagePickerButtonText}>Tirar Foto</Text>
        </TouchableOpacity>
      </View>

      {image && <Image source={{ uri: image }} style={styles.previewImage} />}

      <TouchableOpacity
        style={styles.submitButton}
        onPress={handleSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>Enviar Problema</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.cancelButton}
        onPress={() => navigation.goBack()}
        disabled={loading}
      >
        <Text style={styles.cancelButtonText}>Cancelar</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#26326D',
    marginBottom: 20,
    textAlign: 'center',
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#546E7A',
    marginBottom: 8,
    marginTop: 15,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 10,
  },
  readOnlyInput: {
    backgroundColor: '#e0e0e0',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 10,
    color: '#666',
  },
  textArea: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    textAlignVertical: 'top', // Para Android
    marginBottom: 10,
  },
  imagePickerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
    marginTop: 10,
  },
  imagePickerButton: {
    backgroundColor: '#00B0FF',
    padding: 12,
    borderRadius: 8,
    flex: 1,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  imagePickerButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  previewImage: {
    width: '100%',
    height: 200,
    resizeMode: 'cover',
    borderRadius: 8,
    marginBottom: 20,
  },
  submitButton: {
    backgroundColor: '#28a745', // Verde para sucesso
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 20,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButton: {
    backgroundColor: '#dc3545', // Vermelho para cancelar
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default RelatarProblemaScreen;