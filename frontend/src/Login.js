// src/Login.js
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

import {
    Form,
    Stack,
    TextArea,
    FormGroup,
    TextInput,
    Button,
    ToastNotification
  } from '@carbon/react';

function Login() {
  const server_host = `${process.env.REACT_APP_BE_API_URL}`;
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [eligibleUsers, setEligibleUsers] = useState([
    {username: 'ibm', password: 'ibm'},
    {username: 'fadly', password: 'fadly'},
    {username: 'adit', password: 'adit'},
    {username: 'zano', password: 'zano'},
    {username: 'yujin', password: 'yujin'},
    {username: 'dita', password: 'dita'},
    {username: 'bisma', password: 'bisma'},
    {username: 'indoagri1', password: 'indoagri1'},
    {username: 'indoagri2', password: 'indoagri2'},
    {username: 'indoagri3', password: 'indoagri3'}
  ]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleUsernameChange = (e) => setUsername(e.target.value);
  const handlePasswordChange = (e) => setPassword(e.target.value);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
        const loginForm = { username: username, password: password };
        const loginResponse = await axios.post(server_host + "/login", loginForm);
        
        if(loginResponse.data.result == "eligible") {
            sessionStorage.setItem('username', username);
            navigate('/home');  // Redirect to the "Home" page
        } else {
            setError('Invalid email or password');
        }
      // Redirect to another page or store token
    } catch (error) {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="login-container">
      
      <Form aria-label="sample form" style={{maxWidth: '400px', margin: '100px auto', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'}}>
      <h2>Login</h2>
      <p> </p>
      <Stack id="stack" gap={7}>
      <TextInput id="username" labelText="Username" onChange={handleUsernameChange} value={username} placeholder="Input your username" />
      <TextInput id="password" labelText="Password" onChange={handlePasswordChange} value={password} type="password" placeholder="Input your password"  />
      <Button style={{left: '0', top: '0'}} type="submit" className="some-class" onClick={handleSubmit}>
        Submit
      </Button>
      {error != '' && (
        <ToastNotification title="Error" subtitle={error} ></ToastNotification>
      )}
      </Stack>
      </Form>
      
    </div>
  );
}

export default Login;