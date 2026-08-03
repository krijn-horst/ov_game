import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Layout.css";

const Layout = () => {
    const {
        user,
        isGuest,
        logout
    } = useAuth();

    return (

        <div className="app-container">

            <nav className="navbar">

                <div className="logo">
                    🚆 OV Quest
                </div>

                <div className="nav-links">

                    <Link to="/home">
                        Home
                    </Link>

                    <Link to="/routes">
                        Routes
                    </Link>

                    {
                        !isGuest && user && (
                            <>
                                <Link to="/profile">
                                    Profile
                                </Link>

                                <Link to="/achievements">
                                    Achievements
                                </Link>
                            </>
                        )
                    }

                    {
                        user && (
                            <button
                                onClick={logout}
                            >
                                Logout
                            </button>
                        )
                    }

                    {
                        isGuest && (
                            <Link to="/login">
                                Login
                            </Link>
                        )
                    }

                </div>
            </nav>

            <main>
                <Outlet />
            </main>

        </div>

    );
};
export default Layout;