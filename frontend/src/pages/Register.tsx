import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Register.css";


const Register = () => {

    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [errorField, setErrorField] = useState("");

    const { register } = useAuth();

    const navigate = useNavigate();



    const handleRegister = (e: React.FormEvent) => {

        e.preventDefault();

        setError("");
        setErrorField("");


        const errorMessage = register(
            username,
            email,
            password
        );


        if (errorMessage) {

            setError(errorMessage);


            if (errorMessage.includes("Username")) {
                setErrorField("username");
            }


            if (errorMessage.includes("Email")) {
                setErrorField("email");
            }


            return;

        }


        navigate("/login");

    };



    return (

        <div className="register-container">

            <div className="register-card">


                <h1>
                    OV Quest
                </h1>


                <p className="subtitle">
                    Create an account
                </p>



                <form onSubmit={handleRegister}>


                    <div className="form-group">

                        <label>
                            Username
                        </label>


                        <input

                            className={
                                errorField === "username"
                                    ? "input-error"
                                    : ""
                            }

                            type="text"

                            placeholder="Choose a username"

                            value={username}

                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError("");
                                setErrorField("");
                            }}

                            required

                        />

                    </div>




                    <div className="form-group">

                        <label>
                            Email
                        </label>


                        <input

                            className={
                                errorField === "email"
                                    ? "input-error"
                                    : ""
                            }

                            type="email"

                            placeholder="Enter your email"

                            value={email}

                            onChange={(e) => {
                                setEmail(e.target.value);
                                setError("");
                                setErrorField("");
                            }}

                            required

                        />

                    </div>




                    <div className="form-group">

                        <label>
                            Password
                        </label>


                        <input

                            type="password"

                            placeholder="Choose a password"

                            value={password}

                            onChange={(e) =>
                                setPassword(e.target.value)
                            }

                            required

                        />

                    </div>




                    {
                        error && (

                            <p className="error-message">
                                {error}
                            </p>

                        )
                    }



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