import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from './telas/LoginScreen.js';
import { StyleSheet, Text, View } from 'react-native'; // Adicione esta linha

const Stack = createStackNavigator();

const HomeScreen = ({ route }) => {
  const { userData } = route.params;
  
  return (
    <View style={styles.container}>
      <Text style={styles.welcome}>Bem-vindo, {userData.fullName}!</Text>
      <Text>Tipo de usuário: {userData.userType}</Text>
      <Text>Nível de acesso: {userData.accessLevel}</Text>
    </View>
  );
};

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen 
          name="Login" 
          component={LoginScreen} 
          options={{ headerShown: false }} 
        />
        <Stack.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ title: 'Dashboard' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  welcome: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15
  }
});