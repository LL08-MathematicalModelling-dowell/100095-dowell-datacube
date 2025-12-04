import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { UserPlus } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import api from '../services/api';
import useAuthStore from '../store/authStore.ts';

const registerSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters').trim(),
  lastName: z.string().min(2, 'Last name must be at least 2 characters').trim(),
  email: z.email('Invalid email address').trim(),
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: RegisterForm) => api.post('/core/register', data),

    onSuccess: (response: { message: string; access: string; refresh:string, firstName: string }) => {
      setErrorMessage(null);

      if (response.access) {
        setAuth(response.access,response.refresh, response.firstName);
        setSuccessMessage(response.message || "Registration successful! Redirecting...");
        setTimeout(() => navigate('/overview'), 1500);
      } else {
        const finalMessage = response.message || "Registration successful! Please log in.";
        setSuccessMessage(finalMessage);

        setTimeout(() => navigate('/login'), 2500);
      }
    },

    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : 'Registration failed. Please try again.';

      setErrorMessage(message);
    },
  });


  const onSubmit = (data: RegisterForm) => {
    setErrorMessage(null); // Clear previous errors on submit
    mutation.mutate(data);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans p-4">
      <div className="p-8 bg-slate-800/70 rounded-xl shadow-2xl border border-slate-700 w-full max-w-md backdrop-blur-sm">
        {successMessage ? (
          // Success Screen
          <div className="text-center py-6">
            <UserPlus className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-white mb-4">Success!</h2>
            <p className="mb-8 text-slate-300 font-medium">{successMessage}</p>
            <Link
              to="/login"
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 px-8 rounded-lg transition duration-300 shadow-md shadow-cyan-900/50 hover:shadow-lg hover:shadow-cyan-900/80"
            >
              Go to Login
            </Link>
          </div>
        ) : (
          // Registration Form
          <>
            <div className="flex justify-center mb-6">
              <UserPlus className="w-8 h-8 text-cyan-500" />
            </div>
            <h2 className="text-3xl font-extrabold text-white mb-8 text-center tracking-wider">
              Create Account
            </h2>

            {/* Dynamic Error Display */}
            {errorMessage && (
              <div className="mb-6 p-3 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm text-center shadow-inner">
                {/* <p className="font-medium">Registration Error:</p> */}
                <p>{errorMessage}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* First Name */}
              <div>
                <input
                  id="firstName"
                  {...register('firstName')}
                  placeholder="First Name"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.firstName ? 'true' : 'false'}
                />
                {errors.firstName && (
                  <p className="text-red-400 text-sm mt-1 font-mono">{errors.firstName.message}</p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <input
                  id="lastName"
                  {...register('lastName')}
                  placeholder="Last Name"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.lastName ? 'true' : 'false'}
                />
                {errors.lastName && (
                  <p className="text-red-400 text-sm mt-1 font-mono">{errors.lastName.message}</p>
                )}
              </div>

              {/* Email Address */}
              <div>
                <input
                  id="email"
                  type="email"
                  {...register('email')}
                  placeholder="Email Address"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.email ? 'true' : 'false'}
                />
                {errors.email && (
                  <p className="text-red-400 text-sm mt-1 font-mono">{errors.email.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <input
                  id="password"
                  type="password"
                  {...register('password')}
                  placeholder="Password (8+ chars, Uppercase, Number, Symbol)"
                  className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition-colors"
                  aria-invalid={errors.password ? 'true' : 'false'}
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1 font-mono">{errors.password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={mutation.isPending}
                className="w-full mt-6 bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded-lg transition duration-300 shadow-md shadow-cyan-900/50 hover:shadow-lg hover:shadow-cyan-900/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {mutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
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
