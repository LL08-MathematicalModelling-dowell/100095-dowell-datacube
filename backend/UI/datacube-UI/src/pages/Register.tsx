import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore.ts';
import { z } from 'zod';
import api from '../services/api';

// Define validation schema with Zod
const registerSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters').trim(),
  lastName: z.string().min(2, 'Last name must be at least 2 characters').trim(),
  email: z.string().email('Invalid email address').trim(),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
  // .regex(
  //   /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$/,
  //   'Password must include uppercase, lowercase, number, and special character'
  // ),
});

type RegisterForm = z.infer<typeof registerSchema>;

const Register = () => {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form setup with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  // Register mutation

  const mutation = useMutation({
    mutationFn: (data: RegisterForm) => api.post('/core/register', data),
    onSuccess: (response: { message: string; access: string; firstName: string }) => {
      setAuth(response.access, response.firstName);
      setSuccessMessage(response.message);
      setTimeout(() => navigate('/overview'), 2000); // Auto-redirect after 2s
    },
    onError: (error: unknown) => {
      const errorMessage =
        error && typeof error === 'object' && 'message' in error
          ? (error as { message?: string }).message
          : 'Registration failed. Please try again.';
      alert(errorMessage); // Consider using a more integrated toast/notification system
    },
  });


  const onSubmit = (data: RegisterForm) => {
    mutation.mutate(data);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans">
      <div className="p-8 bg-slate-800/70 rounded-lg shadow-xl border border-slate-700 w-full max-w-md">
        {successMessage ? (
          <div className="text-center">
            <h2 className="text-3xl font-bold text-white mb-4">Registration Successful!</h2>
            <p className="mb-6 text-slate-300">{successMessage}</p>
            <Link
              to="/login"
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 px-6 rounded-md transition-colors duration-200"
            >
              Go to Login
            </Link>
          </div>
        ) : (
          <>
            <h2 className="text-3xl font-bold text-white mb-6 text-center">Create Your DataCube Account</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-slate-300 mb-1">
                  First Name
                </label>
                <input
                  id="firstName"
                  {...register('firstName')}
                  placeholder="First Name"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.firstName ? 'true' : 'false'}
                />
                {errors.firstName && (
                  <p className="text-red-400 text-sm mt-1">{errors.firstName.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-slate-300 mb-1">
                  Last Name
                </label>
                <input
                  id="lastName"
                  {...register('lastName')}
                  placeholder="Last Name"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.lastName ? 'true' : 'false'}
                />
                {errors.lastName && (
                  <p className="text-red-400 text-sm mt-1">{errors.lastName.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-1">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder="Email Address"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.email ? 'true' : 'false'}
                />
                {errors.email && (
                  <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  {...register('password')}
                  placeholder="Password"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-md text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.password ? 'true' : 'false'}
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={mutation.isPending}
                className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {mutation.isPending ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
            <p className="mt-6 text-center text-slate-400 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors">
                Login here
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default Register;
