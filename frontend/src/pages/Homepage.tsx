import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./HomePage.css";


const HomePage = () => {

    const { user, logout } = useAuth();

    const navigate = useNavigate();


    useEffect(() => {

        if (!user) {
            navigate("/login");
        }

    }, [user, navigate]);



    const handleLogout = () => {

        logout();

        navigate("/login");

    };



    if (!user) {
        return null;
    }



    return (

        <div className="home-container">


            <div className="home-card">


                <h1>
                    Welcome, {user.username} 🚆
                </h1>


                <p>
                    Ready for your next journey?
                </p>




                <div className="stats">


                    <div className="stat-box">

                        <h2>
                            Level 1
                        </h2>

                        <p>
                            Explorer
                        </p>

                    </div>




                    <div className="stat-box">

                        <h2>
                            0 XP
                        </h2>

                        <p>
                            Total experience
                        </p>

                    </div>



                </div>




                <button
                    onClick={handleLogout}
                >
                    Logout
                </button>



            </div>


        </div>

    );
};


export default HomePage;