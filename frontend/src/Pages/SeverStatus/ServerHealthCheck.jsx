import { useState, useEffect } from "react";
import { getServerStatus, getAPIServerStatus } from "../../services/api.services";
import { FaServer, FaDatabase } from "react-icons/fa";

function Healthcheck() {
    const [status, setStatus] = useState(null);
    const [apiStatus, setApiStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);

        Promise.all([getServerStatus(), getAPIServerStatus()])
            .then(([serverRes, apiRes]) => {
                setStatus(serverRes.data);
                setApiStatus(apiRes.data);
                setLoading(false);
            })
            .catch((error) => {
                console.error("Error fetching status:", error);
                setLoading(false);
            });

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col min-h-screen text-gray-800 bg-gradient-to-br from-gray-50 to-gray-100">
            <header className="py-8 bg-blue-700 shadow-lg">
                <h1 className="text-4xl font-bold text-center text-white">Health Dashboard</h1>
            </header>

            <main className="flex flex-col items-center justify-center flex-grow p-8 space-y-12">
                {loading ? (
                    <div className="flex items-center justify-center">
                        <div className="w-16 h-16 border-t-4 border-blue-600 border-opacity-50 rounded-full animate-spin"></div>
                    </div>
                ) : (
                    <div className="grid w-full max-w-6xl grid-cols-1 gap-8 lg:grid-cols-2">
                        
                        {status && (
                            <div className="p-6 transition-transform transform bg-white rounded-lg shadow-md hover:scale-105">
                                <div className="flex items-center mb-4">
                                    <FaServer className="text-3xl text-blue-600" />
                                    <h3 className="ml-4 text-2xl font-bold">Server Status</h3>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">Server:</p>
                                    <p className={`${status.success ? 'text-green-500' : 'text-red-500'}`}>
                                        {status.success ? "Online" : "Offline"}
                                    </p>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">Status:</p>
                                    <p>{status.status}</p>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">Version:</p>
                                    <p>{status.version}</p>
                                </div>
                                <p className="text-gray-500">{status.message}</p>
                                <div className="text-sm text-gray-400">
                                    <p>Current Time: {currentTime.toLocaleTimeString()}</p>
                                    <p>Server Time: {new Date(status.server_time).toLocaleTimeString()}</p>
                                </div>
                            </div>
                        )}

                        {apiStatus && (
                            <div className="p-6 transition-transform transform bg-white rounded-lg shadow-md hover:scale-105">
                                <div className="flex items-center mb-4">
                                    <FaDatabase className="text-3xl text-blue-600" />
                                    <h3 className="ml-4 text-2xl font-bold">API Server Status</h3>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">API Server:</p>
                                    <p className={`${apiStatus.success ? 'text-green-500' : 'text-red-500'}`}>
                                        {apiStatus.success ? "Online" : "Offline"}
                                    </p>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">Status:</p>
                                    <p>{apiStatus.status}</p>
                                </div>
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-gray-600">Version:</p>
                                    <p>{apiStatus.version}</p>
                                </div>
                                <p className="text-gray-500">{apiStatus.message}</p>
                                <div className="text-sm text-gray-400">
                                    <p>Current Time: {currentTime.toLocaleTimeString()}</p>
                                    <p>Server Time: {new Date(apiStatus.server_time).toLocaleTimeString()}</p>
                                </div>
                            </div>
                        )}

                   
                        {!status && !apiStatus && (
                            <div className="col-span-2 text-xl text-center text-red-600">
                                Failed to fetch server or API status.
                            </div>
                        )}
                    </div>
                )}
            </main>

            <footer className="py-6 text-center text-white bg-blue-700 shadow-md">
                <p>&copy; 2024 uxlivinglab</p>
            </footer>
        </div>
    );
}

export default Healthcheck;