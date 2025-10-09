import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api.ts';
import useAuthStore from '../store/authStore.ts';
import { Link, useNavigate } from 'react-router-dom';

interface FormData { email: string; password: string; }

const Login = () => {
  const { register, handleSubmit } = useForm<FormData>();
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const mutation = useMutation({
    mutationFn: (data: FormData) => api.post('/core/login', data), // Assume Django endpoint
    onSuccess: (response: { access: string; firstName: string }) => {
      setAuth(response.access, response.firstName);
      navigate('/overview');
    },
    onError: (error) => {
      console.error("Login failed:", error);
      alert('Login failed. Please check your credentials and try again, if error persists contact support.');
    }
  });

  const onSubmit = (data: FormData) => mutation.mutate(data);

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans">
      <form onSubmit={handleSubmit(onSubmit)} className="p-8 bg-slate-800/70 rounded-lg shadow-xl border border-slate-700 w-full max-w-sm">
        <h2 className="text-3xl font-bold text-white mb-6 text-center">Login to DataCube</h2>

        <div className="mb-4">
          <input
            {...register('email', { required: true })}
            type="email"
            placeholder="Email Address"
            className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
          />
        </div>

        <div className="mb-6">
          <input
            {...register('password', { required: true })}
            type="password"
            placeholder="Password"
            className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
          />
        </div>

        <button
          type="submit"
          className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? 'Logging in...' : 'Login'}
        </button>

        {mutation.isError && (
          <p className="mt-4 text-red-400 text-sm text-center">Login failed. Please check your credentials.</p>
        )}

        <p className="mt-6 text-center text-slate-400 text-sm">
          Don't have an account? <Link to="/register" className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors">Register here</Link>
        </p>
      </form>
    </div>
  );
};

export default Login;