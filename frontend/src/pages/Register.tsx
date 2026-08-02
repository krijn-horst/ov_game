import { useState } from "react";
import { Link } from "react-router-dom";
import "./Register.css";

const Register = () => {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [errorField, setErrorField] = useState("");

    const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();

    const existingUsers = JSON.parse(
        sessionStorage.getItem("users") || "[]"
    );

    const usernameExists = existingUsers.some(
        (user: any) => user.username === username
    );

    const emailExists = existingUsers.some(
        (user: any) => user.email === email
    );


    if (usernameExists) {
        setError("Username already exists");
        setErrorField("username");
        return;
    }


    if (emailExists) {
        setError("Email already exists");
        setErrorField("email");
        return;
    }


    const newUser = {
        username,
        email,
        password,
    };


    existingUsers.push(newUser);


    sessionStorage.setItem(
        "users",
        JSON.stringify(existingUsers)
    );


    alert("Account created!");


    window.location.href = "/login";
};

    return (
        <div className="register-container">

            <div className="register-card">

                <h1>OV Quest</h1>

                <p className="subtitle">
                    Create an account
                </p>

                <form onSubmit={handleRegister}>

                    <div className="form-group">

                        <label>Username</label>

                        <input
                            className={
                                errorField === "username"
                                ? "input-error"
                                : ""
                            }

                            type="text"

                            value={username}

                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError("");
                                setErrorField("");
                            }}
                        />

                    </div>

                    <div className="form-group">

                        <label>Email</label>

                        <input
                            className={
                                errorField === "email"
                                ? "input-error"
                                : ""
                            }

                            type="email"

                            value={email}

                            onChange={(e) => {
                                setEmail(e.target.value);
                                setError("");
                                setErrorField("");
                            }}
                        />

                    </div>

                    <div className="form-group">

                        <label>Password</label>

                        <input
                            type="password"
                            placeholder="Choose a password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />

                    </div>

                    {error && (
                        <p className="error-message">
                            {error}
                        </p>
                    )}

                        <button type="submit">
                        Register
                    </button>

                </form>

                <div className="divider" />

                <p className="register">

                    Already have an account?

                    <Link to="/login">
                        Login
                    </Link>

                </p>

            </div>

        </div>
    );
};

export default Register;