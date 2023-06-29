import React, { useState } from "react";
import api from "./api";
import { useNavigate, Link } from "react-router-dom";

function RegisterForm() {
  const [full_name, setFullName] = useState("");
  const [username, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await api.post("/auth/signup", {
        full_name,
        username,
        email,
        phone,
        password,
      });
      const { data } = response;
      console.log(data);
      setFullName("");
      setUserName("");
      setEmail("");
      setPhone("");
      setPassword("");
    } catch (error) {
      console.error("Some fields are incomplete.");
    }
    navigate("/login");
  };
  return (
    <div className="wrapper text-center">
      <div className="formImg"></div>
      <form onSubmit={handleSubmit}>
        <div className="inputField">
          <h2>Create an Account</h2>
          <div class="mb-3">
            <input
              type="name"
              value={full_name}
              onChange={(e) => setFullName(e.target.value)}
              class="form-control"
              id="name"
              placeholder="Full name"
            />
          </div>
          <div class="mb-3">
            <input
              type="username"
              value={username}
              onChange={(e) => setUserName(e.target.value)}
              class="form-control"
              id="username"
              placeholder="Username"
            />
          </div>
          <div class="mb-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              class="form-control"
              id="email"
              placeholder="Email Address"
            />
          </div>
          <div class="mb-3">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              class="form-control"
              id="password"
              placeholder="Password"
            />
          </div>
          <button type="button" class="btn btn-primary" onClick={handleSubmit}>
            Register
          </button>
        </div>
        <div class="mb-3 text-center" id="regLink">
          <p>
            Already have an account? <Link to="/login">Please Login</Link>
          </p>
        </div>
      </form>
    </div>
  );
}

export default RegisterForm;
